"""Pure price indicators. No network, LLM, or implicit trading orders."""
from dataclasses import dataclass, replace
from datetime import date
from math import isfinite, sqrt
from statistics import mean


@dataclass(frozen=True)
class Bar:
    date: date
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        values=(self.open,self.high,self.low,self.close)
        if not all(isfinite(v) and v>0 for v in values) or self.low>min(values) or self.high<max(values):
            raise ValueError('Invalid OHLC')


def adjust_bars(bars, events):
    """Back-adjust all OHLC. Dividend is per pre-split share on ex-date."""
    out=list(bars)
    for event in sorted(events,key=lambda e:e['date']):
        day=date.fromisoformat(event['date'])
        if not out or day>out[-1].date: continue
        before=[b for b in out if b.date<day]
        split=float(event.get('split',1)); dividend=float(event.get('dividend',0))
        if split<=0 or dividend<0: raise ValueError('Invalid event')
        if not before: continue
        ref=before[-1].close
        factor=(ref-dividend)/ref/split
        if not 0<factor<=10: raise ValueError('Invalid adjustment factor')
        out=[replace(b,open=b.open*factor,high=b.high*factor,low=b.low*factor,close=b.close*factor) if b.date<day else b for b in out]
    return out


def smooth(values, n, alpha):
    out=[]; current=None; seed=[]
    for value in values:
        if value is None:
            out.append(None); continue
        if current is None:
            seed.append(value)
            if len(seed)==n: current=mean(seed)
        else: current+=alpha*(value-current)
        out.append(current)
    return out


def cross(previous_a,previous_b,a,b):
    if None in (previous_a,previous_b,a,b): return None
    if previous_a<=previous_b and a>b: return 'golden'
    if previous_a>=previous_b and a<b: return 'death'
    return None


def indicator_series(bars):
    if any(a.date>=b.date for a,b in zip(bars,bars[1:])): raise ValueError('Bars must be unique and sorted')
    c=[b.close for b in bars]; count=len(c)
    e12=smooth(c,12,2/13); e26=smooth(c,26,2/27)
    macd=[a-b if a is not None and b is not None else None for a,b in zip(e12,e26)]
    signal=smooth(macd,9,2/10)
    gains=[None]+[max(c[i]-c[i-1],0) for i in range(1,count)]
    losses=[None]+[max(c[i-1]-c[i],0) for i in range(1,count)]
    avg_gain=smooth(gains,14,1/14); avg_loss=smooth(losses,14,1/14)
    tr=[None]; plus=[None]; minus=[None]
    for i in range(1,count):
        b,p=bars[i],bars[i-1]; up=b.high-p.high; down=p.low-b.low
        tr.append(max(b.high-b.low,abs(b.high-p.close),abs(b.low-p.close)))
        plus.append(up if up>down and up>0 else 0); minus.append(down if down>up and down>0 else 0)
    atr=smooth(tr,14,1/14); pdm=smooth(plus,14,1/14); mdm=smooth(minus,14,1/14)
    pdi=[100*p/a if a else 0 if a==0 else None for p,a in zip(pdm,atr)]
    mdi=[100*m/a if a else 0 if a==0 else None for m,a in zip(mdm,atr)]
    dx=[100*abs(p-m)/(p+m) if p+m else 0 if p is not None else None for p,m in zip(pdi,mdi) if p is not None]
    # ADX starts only after the directional movement seed exists.
    dx=[None]*(count-len(dx))+dx
    adx=smooth(dx,14,1/14)
    result=[]; k=d=50.; rsv=50.
    for i,b in enumerate(bars):
        ma50=mean(c[i-49:i+1]) if i>=49 else None
        ma200=mean(c[i-199:i+1]) if i>=199 else None
        rsi=None
        if avg_loss[i] is not None:
            rsi=50 if avg_loss[i]==avg_gain[i]==0 else 100 if avg_loss[i]==0 else 100-100/(1+avg_gain[i]/avg_loss[i])
        if i>=8:
            high=max(x.high for x in bars[i-8:i+1]); low=min(x.low for x in bars[i-8:i+1])
            if high>low: rsv=100*(b.close-low)/(high-low)
            k=2*k/3+rsv/3; d=2*d/3+k/3
        mid=mean(c[i-19:i+1]) if i>=19 else None
        std=sqrt(mean([(x-mid)**2 for x in c[i-19:i+1]])) if mid is not None else None
        result.append({'rsi':rsi,'k':k if i>=8 else None,'d':d if i>=8 else None,
          'ma50':ma50,'ma200':ma200,'ma200Past':mean(c[i-219:i-19]) if i>=219 else None,
          'macd':macd[i],'signal':signal[i],'hist':macd[i]-signal[i] if signal[i] is not None else None,
          'bbUpper':mid+2*std if mid is not None else None,'bbLower':mid-2*std if mid is not None else None,
          'drawdown':100*(max(c[max(0,i-251):i+1])-b.close)/max(c[max(0,i-251):i+1]),
          'adx':adx[i],'plusDI':pdi[i],'minusDI':mdi[i],'atrPct':100*atr[i]/b.close if atr[i] is not None else None})
    return result


def indicators(bars):
    return indicator_series(bars)[-1]


def score_at(bars, values, i):
    v=values[i]; p=values[i-1]; c=bars[i].close
    up=c>v['ma200'] and v['ma200']>v['ma200Past'] and v['ma50']>v['ma200']
    down=c<v['ma200'] and v['ma200']<v['ma200Past'] and v['ma50']<v['ma200']
    trend=8 if up else 2 if down else 5
    draw=4 if v['drawdown']<5 else 6 if v['drawdown']<10 else 8
    rsi=8 if p['rsi']<=30<v['rsi'] else 6 if 40<=v['rsi']<=60 and v['rsi']>p['rsi'] else 4 if v['rsi']<30 and v['rsi']<p['rsi'] else 5
    kd_cross=cross(p['k'],p['d'],v['k'],v['d'])
    kd=8 if kd_cross=='golden' and max(v['k'],v['d'])<20 else 2 if kd_cross=='death' and min(v['k'],v['d'])>80 else 6 if v['k']>v['d'] else 5
    bb=8 if bars[i-1].close<p['bbLower'] and c>=v['bbLower'] else 4 if c<v['bbLower'] else 5
    hist=v['hist']; previous=p['hist']
    momentum=5 if hist==previous or hist==0 else 8 if hist>0 and hist>previous else 6 if hist>0 else 4 if hist>previous else 2
    timing=mean([rsi,kd,bb]); parts={'trend':trend,'drawdown':draw,'timing':timing,'momentum':momentum}
    raw=trend*.4+draw*.25+timing*.25+momentum*.1
    falling=c<v['ma200'] and v['ma200']<v['ma200Past']
    cap=5 if falling and v['adx']>=25 and v['minusDI']>v['plusDI'] else 6 if falling else 10
    buy=min(raw,cap)
    rsi_sell=8 if p['rsi']>=70>v['rsi'] else 5
    kd_sell=8 if kd_cross=='death' and min(v['k'],v['d'])>80 else 2 if kd_cross=='golden' and max(v['k'],v['d'])<20 else 6 if v['k']<v['d'] else 5
    bb_sell=8 if bars[i-1].close>p['bbUpper'] and c<=v['bbUpper'] else 5
    trend_sell=8 if falling else 2 if up else 5
    sell=trend_sell*.5+mean([rsi_sell,kd_sell,bb_sell])*.3+(10-momentum)*.2
    details=[('長期均線',trend,trend_sell,f"SMA50 {v['ma50']:.2f} · SMA200 {v['ma200']:.2f}"),
      ('高點回落',draw,None,f"距252日高點 −{v['drawdown']:.2f}%"),
      ('RSI (14)',rsi,rsi_sell,f"RSI {v['rsi']:.2f}"),('KD (9, 1/3)',kd,kd_sell,f"K {v['k']:.2f} · D {v['d']:.2f}"),
      ('布林通道 (20, 2)',bb,bb_sell,f"下軌 {v['bbLower']:.2f} · 上軌 {v['bbUpper']:.2f}"),
      ('MACD (12, 26, 9)',momentum,10-momentum,f"Histogram {hist:.3f}"),
      ('ADX / DMI (14)',None,None,f"ADX {v['adx']:.2f} · +DI {v['plusDI']:.2f} · −DI {v['minusDI']:.2f}"),
      ('ATR 波動率 (14)',None,None,f"ATR / 收盤 {v['atrPct']:.2f}%")]
    return {'buyScore':round(buy,1),'sellScore':round(sell,1),'rawBuyScore':round(raw,2),'cap':cap,'parts':parts,
      'qualifies':buy>=7 and sum(s>=6 for s in parts.values())>=3,
      'details':[{'name':name,'buyScore':b,'sellScore':s,'value':value} for name,b,s,value in details],
      'cross':cross(p['ma50'],p['ma200'],v['ma50'],v['ma200'])}


def analyze(bars):
    if len(bars)<400: return {'buyScore':None,'sellScore':None,'confirmed':False,'count':len(bars),'details':[]}
    values=indicator_series(bars); i=len(bars)-1
    result=score_at(bars,values,i)
    result['confirmed']=all(score_at(bars,values,j)['qualifies'] for j in range(i-2,i+1))
    result['indicators']=values[-1]; result['count']=len(bars)
    return result
