"""Free research providers. Fetching is separate from publication permission."""
import csv
import io
import json
import math
import time
import urllib.request
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo
from market.engine import Bar
from market.sessions import calendar

SYMBOLS={'taiex':'^TWII','2330':'2330.TW','0050':'0050.TW','00631L':'00631L.TW','00685L':'00685L.TW','sp500':'^GSPC','nasdaq':'^IXIC','kospi':'^KS11','nikkei':'^N225'}


def fetch_text(url):
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; HuaxiMarketJournal/1.0)'})
            with urllib.request.urlopen(req,timeout=25) as response:return response.read().decode('utf-8-sig')
        except OSError as exc:
            if getattr(exc,'code',0) in {401,403,418} or attempt==2: raise
            time.sleep(2**attempt)


def parse_yahoo(payload,cutoff):
    chart=payload.get('chart',{});results=chart.get('result')
    if chart.get('error') or not results:raise ValueError('Yahoo chart unavailable')
    result=results[0];zone=ZoneInfo(result['meta']['exchangeTimezoneName'])
    prices=result['indicators']['quote'][0]
    adjusted=result['indicators'].get('adjclose',[{}])[0].get('adjclose',[])
    bars=[];raw=[]
    for i,stamp in enumerate(result.get('timestamp',[])):
        day=datetime.fromtimestamp(stamp,zone).date()
        if day>cutoff:continue
        try:
            values=[float(prices[k][i]) for k in ['open','high','low','close']]
            adj=float(adjusted[i]);factor=adj/values[3]
            if not math.isfinite(factor) or factor<=0:raise ValueError('Invalid adjustment')
            bar=Bar(day,*[v*factor for v in values])
            bars.append({'date':day.isoformat(),'open':bar.open,'high':bar.high,'low':bar.low,'close':bar.close})
            raw.append({'date':day.isoformat(),'close':values[3]})
        except (ValueError,TypeError,IndexError,KeyError,ZeroDivisionError):continue
    if not bars:raise ValueError('No complete Yahoo OHLC with adjusted close')
    if len({b['date'] for b in bars})!=len(bars):raise ValueError('Duplicate provider sessions')
    change=(raw[-1]['close']/raw[-2]['close']-1)*100 if len(raw)>1 else None
    return {'bars':bars,'priceBasis':'vendor-adjusted','quoteSnapshot':{**raw[-1],'changePct':change},
      'eventsReviewedThrough':bars[-1]['date'],'events':[],
      'sourceName':'Yahoo Finance · 免費研究來源','sourceUrl':'https://finance.yahoo.com/',
      'licenseNote':'Yahoo資料使用條款適用；接入或使用者選擇不代表取得再散布授權。'}


def fetch_yahoo(asset,cutoff):
    symbol=SYMBOLS[asset]
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol,safe="")}?range=5y&interval=1d&events=div%2Csplits'
    return parse_yahoo(json.loads(fetch_text(url)),cutoff)


def parse_vix(text,cutoff):
    rows=[]
    for row in csv.DictReader(io.StringIO(text)):
        day=datetime.strptime(row['DATE'],'%m/%d/%Y').date()
        if day>cutoff:continue
        value=float(row['CLOSE'])
        if not math.isfinite(value) or value<0:raise ValueError('Invalid VIX')
        rows.append((day,value))
    if not rows:raise ValueError('No completed VIX value')
    day,value=sorted(rows)[-1]
    return {'id':'vix','name':'VIX 波動率','label':'市場的心跳','value':value,'sessionDate':day.isoformat(),
      'status':'已收盤' if day==cutoff else '來源更新落後','url':'https://www.cboe.com/tradable_products/vix/'}


def fetch_vix(cutoff):
    return parse_vix(fetch_text('https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv'),cutoff)


def parse_cnn(payload,cutoff):
    fg=payload['fear_and_greed'];score=float(fg['score']);stamp=fg['timestamp']
    dt=datetime.fromtimestamp(stamp/1000,ZoneInfo('America/New_York')) if isinstance(stamp,(int,float)) else datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York'))
    cal=calendar('us',dt.year)
    if not 0<=score<=100 or not math.isfinite(score) or dt.date()>cutoff or not cal.is_session(dt.date().isoformat()):
        raise ValueError('CNN snapshot is not a confirmed post-close observation')
    if dt<cal.session_close(dt.date().isoformat()).to_pydatetime():
        raise ValueError('CNN snapshot precedes exchange close')
    return {'id':'fear','name':'CNN 恐慌貪婪','label':'情緒的溫度','value':score,'sessionDate':dt.date().isoformat(),
      'status':str(fg.get('rating','收盤後觀察')),'url':'https://www.cnn.com/markets/fear-and-greed'}


def fetch_cnn(cutoff):
    return parse_cnn(json.loads(fetch_text('https://production.dataviz.cnn.io/index/fearandgreed/graphdata')),cutoff)
