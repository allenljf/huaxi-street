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
    eligible=bool(latest) and (meta['kind']=='index' or record.get('eventsReviewedThrough','')>=latest.date.isoformat())
    adjusted=adjust_bars(bars,record.get('events',[])) if eligible else []
    report=analyze(adjusted)
    can_score=meta['region']=='tw' and not stale and eligible and len(adjusted)>=400
    reason='免費分享資料源待確認' if meta['region']!='tw' else f'指標資料累積中 · {len(bars)} / 400 交易日'
    if latest and not eligible: reason='分割／配息調整資料待補齊'
    if stale: reason='行情尚未更新至最近完整交易日'
    if can_score:
        reason='長期趨勢與進場節奏綜合觀察'
        if report['cap']<10: reason=f"長期趨勢偏弱，陪葬分上限 {report['cap']}"
    if error: reason='更新未完成，顯示上次成功資料' if latest else '資料來源暫時無法連線'
    change=(latest.close/bars[-2].close-1)*100 if len(bars)>1 else None
    if len(bars)>1 and eligible:
        # Normalize yesterday's reference for today's split/dividend.
        change=(latest.close/adjusted[-2].close-1)*100
    official_change=record.get('quoteChange',{})
    if latest and official_change.get('date')==latest.date.isoformat():
        reference=latest.close-official_change['value']
        if reference>0: change=100*official_change['value']/reference
    return {**meta,'sessionDate':latest.date.isoformat() if latest else None,'close':latest.close if latest else None,
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
      'adjustment':'分割與配息一致調整' if eligible and record.get('events') else '價格指數' if meta['kind']=='index' else '原始收盤價；調整待確認',
      'expectedSession':expected.isoformat() if meta['region']=='tw' else None}


def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp'); temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n'); temp.replace(path)


def build(now=None, offline=False):
    now=now or datetime.now(ZoneInfo('Asia/Taipei'))
    storage=ROOT/'data/history.json'; state=json.loads(storage.read_text()) if storage.exists() else {}
    errors={}; new={}; calendar=ROOT/'data/calendar.json'
    schedule=json.loads(calendar.read_text()) if calendar.exists() else []
    if not offline:
        for endpoint,key in [('holidaySchedule/holidaySchedule','calendar'),('indicesReport/MI_5MINS_HIST','taiex'),('exchangeReport/STOCK_DAY_ALL','stocks')]:
            try:
                payload=fetch_json(endpoint)
                if not isinstance(payload,list) or not payload: raise ValueError('Empty API response')
                new[key]=payload
            except (OSError,ValueError): errors[key]='source unavailable'
        if 'calendar' in new: schedule=new['calendar']; write_json(calendar,schedule)
    holidays={parse_date(r['Date']) for r in schedule if not any(t in r.get('Name','') for t in ['開始交易','最後交易'])}
    expected=expected_session(now,holidays)
    calendar_ok=any(parse_date(r['Date']).year==expected.year for r in schedule)
    for row in new.get('taiex',[]):
        try:
            bar=Bar(parse_date(row['Date']),*[float(row[k].replace(',','')) for k in ['OpeningIndex','HighestIndex','LowestIndex','ClosingIndex']])
            new.setdefault('taiexBars',[]).append(bar)
        except (ValueError,KeyError): errors['taiex']='invalid data'
    for row in new.get('stocks',[]):
        if row.get('Code') not in {c['id'] for c in CATALOG}: continue
        try:
            bar=Bar(parse_date(row['Date']),*[float(row[k].replace(',','')) for k in ['OpeningPrice','HighestPrice','LowestPrice','ClosingPrice']])
            new.setdefault(row['Code']+'Bars',[]).append(bar)
            try:
                difference=float(row['Change'].replace(',',''))
                if bar.date<=expected:
                    new.setdefault('quoteChanges',{})[row['Code']]={'date':bar.date.isoformat(),'value':difference}
            except (KeyError,ValueError): pass
        except (ValueError,KeyError): errors[row.get('Code')]='invalid data'
    markets=[]
    for meta in CATALOG:
        record=state.get(meta['id'],{})
        if meta['id'] in new.get('quoteChanges',{}):
            record={**record,'quoteChange':new['quoteChanges'][meta['id']]}
        bars=merge_bars(deserialize(record.get('bars',[])),new.get(meta['id']+'Bars',[]),expected)
        if meta['region']=='tw' and bars:
            record={**record,'bars':serialize(bars)}; state[meta['id']]=record
        error=errors.get('taiex' if meta['id']=='taiex' else 'stocks') or errors.get(meta['id']) if meta['region']=='tw' else None
        view=market_view(meta,bars,expected,record,error)
        if meta['region']=='tw' and not calendar_ok:
            view.update(status='stale',buyScore=None,sellScore=None,confirmed=False,reasons=['交易日曆尚未更新，暫停新評分'])
        markets.append(view)
    write_json(storage,state)
    output={'version':1,'rulesVersion':'research-v1','generatedAt':now.isoformat(),'expectedTaiwanSession':expected.isoformat(),
      'scheduleText':'每週一至六 08:00 啟動更新' if os.environ.get('INCLUDE_SATURDAY')=='true' else '每週一至五 08:00 啟動更新',
      'markets':markets,'sentiment':[
        {'id':'vix','name':'VIX 波動率','label':'市場的心跳','value':None,'status':'官方來源待確認分享權','url':'https://www.cboe.com/tradable_products/vix/'},
        {'id':'fear','name':'CNN 恐慌貪婪','label':'情緒的溫度','value':None,'status':'資料端點不穩定，先看官方','url':'https://www.cnn.com/markets/fear-and-greed'}],
      'research':{'status':'awaiting-history','note':'歷史與公司行動資料未齊，尚未產生真實回測績效。'}}
    write_json(ROOT/'web/public/data/markets.json',output)
    print(f"Published {len(markets)} market statuses; {sum(m['close'] is not None for m in markets)} quoted; {sum(m['buyScore'] is not None for m in markets)} scored; {len(errors)} source errors.")
    return output


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--offline',action='store_true'); parser.add_argument('--import-bundle',type=Path)
    args=parser.parse_args()
    if args.import_bundle:
        bundle=import_bundle(json.loads(args.import_bundle.read_text())); path=ROOT/'data/history.json'
        state=json.loads(path.read_text()) if path.exists() else {}; state[bundle['id']]=bundle; write_json(path,state)
    build(offline=args.offline)

if __name__=='__main__': main()
