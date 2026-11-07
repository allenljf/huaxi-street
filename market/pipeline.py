"""Only explicitly cleared sources enter the public artifact."""
import argparse
import json
import os
import re
import time
import urllib.request
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from market.engine import Bar, adjust_bars, analyze
from market.sessions import last_completed_session, selected_market, market_key, SCHEDULE_TEXT, next_update_at
from market.providers import fetch_yahoo, fetch_vix, fetch_cnn

ROOT=Path(__file__).resolve().parents[1]
API='https://openapi.twse.com.tw/v1/'
CATALOG=[
 {'id':'taiex','symbol':'TAIEX','name':'台灣加權','en':'TAIWAN WEIGHTED','region':'tw','kind':'index','sourceUrl':'https://www.twse.com.tw/zh/indices/taiex/mi-5min-hist.html'},
 {'id':'2330','symbol':'2330','name':'台積電','en':'TAIWAN SEMICONDUCTOR','region':'tw','kind':'stock','sourceUrl':'https://www.twse.com.tw/zh/trading/historical/stock-day.html'},
 {'id':'0050','symbol':'0050','name':'元大台灣50','en':'YUANTA TAIWAN 50','region':'tw','kind':'etf','sourceUrl':'https://www.yuantaetfs.com/product/detail/0050/Basic_information'},
 {'id':'00631L','symbol':'00631L','name':'元大台灣50正2','en':'TAIWAN 50 · DAILY 2×','region':'tw','kind':'leveraged','sourceUrl':'https://www.yuantaetfs.com/product/detail/00631L/Basic_information'},
 {'id':'00685L','symbol':'00685L','name':'群益臺灣加權正2','en':'TAIWAN WEIGHTED · DAILY 2×','region':'tw','kind':'leveraged','sourceUrl':'https://www.capitalfund.com.tw/etf/product/detail/094'},
 {'id':'sp500','symbol':'SPX','name':'標普500','en':'S&P 500','region':'us','kind':'index','sourceUrl':'https://www.spglobal.com/spdji/en/indices/equity/sp-500/'},
 {'id':'nasdaq','symbol':'IXIC','name':'納斯達克綜合','en':'NASDAQ COMPOSITE','region':'us','kind':'index','sourceUrl':'https://www.nasdaq.com/market-activity/index/comp'},
 {'id':'kospi','symbol':'KOSPI','name':'韓國綜合','en':'KOREA COMPOSITE','region':'asia','kind':'index','sourceUrl':'https://global.krx.co.kr/'},
 {'id':'nikkei','symbol':'N225','name':'日經225','en':'NIKKEI 225','region':'asia','kind':'index','sourceUrl':'https://indexes.nikkei.co.jp/en/nkave'}]


def parse_date(value):
    digits=re.sub(r'\D','',str(value))
    if len(digits)==7: return date(int(digits[:3])+1911,int(digits[3:5]),int(digits[5:]))
    if len(digits)==8: return date(int(digits[:4]),int(digits[4:6]),int(digits[6:]))
    raise ValueError('Invalid date')


def expected_session(now, holidays):
    local=now.astimezone(ZoneInfo('Asia/Taipei'))
    day=local.date() if (local.hour,local.minute)>=(14,0) else local.date()-timedelta(days=1)
    while day.weekday()>=5 or day in holidays: day-=timedelta(days=1)
    return day


def merge_bars(old, new, cutoff):
    return sorted({b.date:b for b in [*old,*new] if b.date<=cutoff}.values(),key=lambda b:b.date)


def deserialize(rows):
    return [Bar(parse_date(b['date']),*[float(b[k]) for k in ['open','high','low','close']]) for b in rows]


def serialize(bars):
    return [{**asdict(b),'date':b.date.isoformat()} for b in bars]


def import_bundle(bundle):
    ids={c['id'] for c in CATALOG}
    if bundle.get('id') not in ids or bundle.get('publicPermission') is not True or not bundle.get('sourceUrl','').startswith('https://') or not bundle.get('licenseNote'):
        raise ValueError('Import needs known id, publicPermission=true, https sourceUrl and licenseNote')
    rows=deserialize(bundle['bars'])
    if not rows: raise ValueError('Empty history')
    if len({b.date for b in rows})!=len(rows): raise ValueError('Duplicate history dates')
    rows.sort(key=lambda b:b.date)
    if parse_date(bundle['eventsReviewedThrough'])<rows[-1].date: raise ValueError('Corporate actions review is out of date')
    # Validate action factors before writing anything.
    adjust_bars(rows,bundle.get('events',[]))
    return {**bundle,'bars':serialize(rows)}


def fetch_json(path):
    for attempt in range(3):
        try:
            request=urllib.request.Request(API+path,headers={'User-Agent':'HuaxiMarketJournal/1.0 (daily open-data research)'})
            with urllib.request.urlopen(request,timeout=25) as response: return json.load(response)
        except (OSError,ValueError):
            if attempt==2: raise
            time.sleep(2**attempt)


def market_view(meta,bars,expected,record,error):
    latest=bars[-1] if bars else None
    stale=latest is not None and latest.date<expected
    eligible=bool(latest) and (record.get('priceBasis')=='vendor-adjusted' or meta['kind']=='index' or record.get('eventsReviewedThrough','')>=latest.date.isoformat())
    adjusted=(bars if record.get('priceBasis')=='vendor-adjusted' else adjust_bars(bars,record.get('events',[]))) if eligible else []
    report=analyze(adjusted)
    can_score=not stale and eligible and len(adjusted)>=400
    reason='免費分享資料源待確認' if meta['region']!='tw' else f'指標資料累積中 · {len(bars)} / 400 交易日'
    if latest and not eligible: reason='分割／配息調整資料待補齊'
    if stale: reason='行情尚未更新至最近完整交易日'
    if can_score:
        reason='長期趨勢與進場節奏綜合觀察'
        if report['cap']<10: reason=f"長期趨勢偏弱，買進分上限 {report['cap']}"
    if error: reason='更新未完成，顯示上次成功資料' if latest else '資料來源暫時無法連線'
    change=(latest.close/bars[-2].close-1)*100 if len(bars)>1 else None
    if len(bars)>1 and eligible:
        # Normalize yesterday's reference for today's split/dividend.
        change=(latest.close/adjusted[-2].close-1)*100
    official_change=record.get('quoteChange',{})
    if latest and official_change.get('date')==latest.date.isoformat():
        reference=latest.close-official_change['value']
        if reference>0: change=100*official_change['value']/reference
    quote=record.get('quoteSnapshot',{})
    display_close=latest.close if latest else None
    if latest and quote.get('date')==latest.date.isoformat():
        display_close=quote['close'];change=quote.get('changePct')
    return {**meta,'sessionDate':latest.date.isoformat() if latest else None,'close':display_close,
      'changePct':round(change,2) if change is not None else None,
      'sparkline':[b.close for b in (adjusted if eligible else bars)[-60:]],
      'history':[{'date':b.date.isoformat(),'close':b.close} for b in (adjusted if eligible else bars)[-252:]],
      'buyScore':report.get('buyScore') if can_score and not error else None,
      'sellScore':report.get('sellScore') if can_score and not error else None,
      'confirmed':report.get('confirmed',False) if can_score and not error else False,
      'leveraged':meta['kind']=='leveraged','status':'stale' if stale or (error and latest) else 'fresh' if latest else 'unavailable',
      'dataCount':len(bars),'scoreStatus':'ready' if can_score and not error else 'warming' if latest else 'unavailable',
      'reasons':[reason],'details':report.get('details',[]) if can_score and not error else [],
      'cross':report.get('cross') if can_score and not error else None,
      'sourceName':record.get('sourceName','TWSE 開放資料' if meta['region']=='tw' else '官方行情'),
      'licenseNote':record.get('licenseNote','政府資料開放授權條款第1版' if meta['region']=='tw' else '尚未確認公開分享資料源'),
      'dataSourceUrl':record.get('sourceUrl','https://openapi.twse.com.tw/' if meta['region']=='tw' else meta['sourceUrl']),
      'adjustment':'來源調整後OHLC（分割／配息）' if record.get('priceBasis')=='vendor-adjusted' else '分割與配息一致調整' if eligible and record.get('events') else '價格指數' if meta['kind']=='index' else '原始收盤價；調整待確認',
      'expectedSession':expected.isoformat(),'lastSuccessfulFetchAt':record.get('lastSuccessfulFetchAt'),
      'lastAttemptedAt':record.get('lastAttemptedAt'),'sourceError':record.get('lastError')}


def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp'); temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n'); temp.replace(path)


def build(now=None, offline=False, batch='all', research=False, publish_research=False):
    now=now or datetime.now(ZoneInfo('Asia/Taipei'))
    # Publication is an explicit switch, separate from fetching for research.
    private=research and not publish_research
    storage=ROOT/('.private/research-history.json' if private else 'data/history.json')
    public_history=ROOT/'data/history.json'
    state=json.loads(storage.read_text()) if storage.exists() else json.loads(public_history.read_text()) if public_history.exists() else {}
    calendar_file=ROOT/'data/calendar.json'
    schedule=json.loads(calendar_file.read_text()) if calendar_file.exists() else []
    errors={};new={};stamp=now.isoformat()
    if not offline and not research and batch in {'all','asia'}:
        for endpoint,key in [('holidaySchedule/holidaySchedule','calendar'),('indicesReport/MI_5MINS_HIST','taiex'),('exchangeReport/STOCK_DAY_ALL','stocks')]:
            try:
                payload=fetch_json(endpoint)
                if not isinstance(payload,list) or not payload:raise ValueError('Empty API response')
                new[key]=payload
            except (OSError,ValueError):errors[key]='資料來源連線或格式異常'
        if 'calendar' in new:schedule=new['calendar'];write_json(calendar_file,schedule)
    holidays={parse_date(r['Date']) for r in schedule if not any(t in r.get('Name','') for t in ['開始交易','最後交易'])}
    expected_by_id={m['id']:last_completed_session(market_key(m['id']),now,holidays if m['region']=='tw' else frozenset()) for m in CATALOG}
    for row in new.get('taiex',[]):
        try:
            bar=Bar(parse_date(row['Date']),*[float(row[k].replace(',','')) for k in ['OpeningIndex','HighestIndex','LowestIndex','ClosingIndex']])
            new.setdefault('taiexBars',[]).append(bar)
        except (ValueError,KeyError):errors['taiex']='資料格式異常'
    for row in new.get('stocks',[]):
        asset=row.get('Code')
        if asset not in expected_by_id:continue
        try:
            bar=Bar(parse_date(row['Date']),*[float(row[k].replace(',','')) for k in ['OpeningPrice','HighestPrice','LowestPrice','ClosingPrice']])
            new.setdefault(asset+'Bars',[]).append(bar)
            try:
                delta=float(row['Change'].replace(',',''))
                if bar.date<=expected_by_id[asset]:new.setdefault('quoteChanges',{})[asset]={'date':bar.date.isoformat(),'value':delta}
            except (KeyError,ValueError):pass
        except (ValueError,KeyError):errors[asset]='資料格式異常'
    markets=[]
    for meta in CATALOG:
        asset=meta['id'];expected=expected_by_id[asset];record=state.get(asset,{})
        selected=selected_market(asset,batch)
        error=None
        if selected and not offline:
            record={**record,'lastAttemptedAt':stamp}
            if research:
                try:
                    record={**record,**fetch_yahoo(asset,expected),'lastSuccessfulFetchAt':stamp,'lastError':None,'provider':'yahoo'}
                    record.pop('quoteChange',None)
                except (OSError,ValueError,KeyError,TypeError):
                    error='免費研究來源暫時無法更新';record['lastError']=error
            elif meta['region']=='tw':
                error=errors.get('taiex' if asset=='taiex' else 'stocks') or errors.get(asset)
                incoming=new.get(asset+'Bars',[])
                # Avoid splicing raw OpenAPI prices onto a previously adjusted vendor series.
                if record.get('priceBasis')=='vendor-adjusted':
                    record={'bars':[], 'lastAttemptedAt':stamp}
                bars=merge_bars(deserialize(record.get('bars',[])),incoming,expected)
                record={**record,'bars':serialize(bars),'lastError':error}
                if incoming and not error:record['lastSuccessfulFetchAt']=stamp
                if asset in new.get('quoteChanges',{}):record['quoteChange']=new['quoteChanges'][asset]
            state[asset]=record
        bars=merge_bars([],deserialize(record.get('bars',[])),expected)
        view=market_view(meta,bars,expected,record,error or record.get('lastError'))
        if meta['region']=='tw' and not research and not any(parse_date(r['Date']).year==expected.year for r in schedule):
            view.update(status='stale',buyScore=None,sellScore=None,confirmed=False,reasons=['交易日曆尚未更新，暫停新評分'])
        fetched_at=record.get('lastSuccessfulFetchAt')
        view['nextUpdateAt']=next_update_at(asset,datetime.fromisoformat(fetched_at) if fetched_at else now)
        markets.append(view)
    sentiment_path=ROOT/('.private/research-sentiment.json' if private else 'data/sentiment.json')
    sentiment_state=json.loads(sentiment_path.read_text()) if sentiment_path.exists() else {}
    if research and batch in {'all','us'} and not offline:
        cutoff=last_completed_session('us',now)
        for asset,fetcher in [('vix',fetch_vix),('fear',fetch_cnn)]:
            previous=sentiment_state.get(asset,{})
            try:sentiment_state[asset]={**fetcher(cutoff),'lastSuccessfulFetchAt':stamp,'lastAttemptedAt':stamp}
            except (OSError,ValueError,KeyError,TypeError):
                sentiment_state[asset]={**previous,'lastAttemptedAt':stamp,'status':'資料來源暫時無法更新；保留前值' if previous.get('value') is not None else '資料來源暫時無法取得'}
    defaults=[{'id':'vix','name':'VIX 波動率','label':'市場的心跳','value':None,'status':'官方來源待確認分享權','url':'https://www.cboe.com/tradable_products/vix/'},
      {'id':'fear','name':'CNN 恐慌貪婪','label':'情緒的溫度','value':None,'status':'資料端點不穩定，先看官方','url':'https://www.cnn.com/markets/fear-and-greed'}]
    sentiment=[{**d,**sentiment_state.get(d['id'],{})} for d in defaults]
    write_json(storage,state);write_json(sentiment_path,sentiment_state)
    output={'version':1,'rulesVersion':'research-v1','generatedAt':stamp,'expectedTaiwanSession':expected_by_id['taiex'].isoformat(),
      'scheduleText':SCHEDULE_TEXT,'lastBatch':batch,'researchSources':research,'privateResearch':private,
      'markets':markets,'sentiment':sentiment,
      'research':{'status':'research-only' if any(m['buyScore'] is not None for m in markets) else 'awaiting-history',
        'note':'技術指標採固定研究規則；尚未產生真實樣本外回測績效。'}}
    write_json(ROOT/('.private/markets.json' if private else 'web/public/data/markets.json'),output)
    print(f"{'PRIVATE research' if private else 'Public'} / {batch}: {sum(m['close'] is not None for m in markets)} quotes, {sum(m['buyScore'] is not None for m in markets)} scores, {sum(m['status']=='stale' for m in markets)} stale.")
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true');parser.add_argument('--import-bundle',type=Path)
    parser.add_argument('--batch',choices=['asia','us','all'],default='all')
    parser.add_argument('--research',action='store_true',help='Fetch free research providers into ignored .private by default')
    parser.add_argument('--publish-research',action='store_true',help='Explicitly publish chosen research-source data; does not grant data rights')
    args=parser.parse_args()
    if args.import_bundle:
        bundle=import_bundle(json.loads(args.import_bundle.read_text()));path=ROOT/'data/history.json'
        state=json.loads(path.read_text()) if path.exists() else {};state[bundle['id']]=bundle;write_json(path,state)
    settings_path=ROOT/'data/provider-settings.json'
    settings=json.loads(settings_path.read_text()) if settings_path.exists() else {}
    research=args.research or (os.environ.get('ENABLE_RESEARCH_SOURCES')=='true' if os.environ.get('ENABLE_RESEARCH_SOURCES') else settings.get('enableResearch',False))
    publish=args.publish_research or (os.environ.get('PUBLISH_RESEARCH_SOURCES')=='true' if os.environ.get('PUBLISH_RESEARCH_SOURCES') else settings.get('publishResearch',False))
    if publish and not research:parser.error('--publish-research requires --research')
    build(offline=args.offline,batch=args.batch,research=research,publish_research=publish)

if __name__=='__main__':main()
