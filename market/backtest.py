"""Research-only equal-cashflow comparison. Prices must be adjusted consistently."""
import argparse
import json
from datetime import date
from math import prod
from pathlib import Path
from market.engine import adjust_bars, indicator_series, score_at
from market.pipeline import ROOT, deserialize, write_json


def xirr(flows):
    if not flows or not any(v<0 for _,v in flows) or not any(v>0 for _,v in flows): return None
    origin=flows[0][0]
    def npv(rate): return sum(v/(1+rate)**((d-origin).days/365) for d,v in flows)
    low=-.9999; high=1.
    for _ in range(30):
        if npv(low)*npv(high)<=0: break
        high=high*2+1
    else: return None
    for _ in range(150):
        mid=(low+high)/2
        if npv(mid)>0: low=mid
        else: high=mid
    return (low+high)/2


def simulate(bars,signals,mode,fee_rate=.001425,minimum_fee=0,slippage=.0005):
    if mode not in {'dca','signal','ma'}: raise ValueError('Unknown strategy')
    cash=units=contributions=previous_value=0.; pending=[]; transactions=[]; flows=[]; returns=[]; curve=[]
    last_month=last_week=None
    for i,b in enumerate(bars):
        month=(b.date.year,b.date.month); week=b.date.isocalendar()[:2]; deposit=0
        if month!=last_month:
            deposit=10000.;cash+=deposit;contributions+=deposit;flows.append((b.date,-deposit))
            if mode!='dca': pending.append([b.date,2000.])
        budget=deposit if mode=='dca' else deposit*.8
        if week!=last_week and mode!='dca':
            previous_day=bars[i-1].date.isoformat() if i else None
            eligible=bool(signals.get(previous_day,False))
            due=[p for p in pending if eligible or (b.date.year-p[0].year)*12+b.date.month-p[0].month>=3]
            budget+=sum(p[1] for p in due)
            pending=[p for p in pending if p not in due]
        if budget>0:
            fee=max(minimum_fee,budget*fee_rate) if fee_rate else 0
            if fee>=budget: raise ValueError('Fee exceeds budget')
            bought=(budget-fee)/(b.open*(1+slippage));units+=bought;cash-=budget
            transactions.append({'date':b.date.isoformat(),'budget':budget,'price':b.open,'fee':fee,'units':bought})
        value=units*b.close+cash
        if previous_value+deposit: returns.append(value/(previous_value+deposit)-1)
        curve.append(prod(1+r for r in returns))
        previous_value=value;last_month=month;last_week=week
    high=1.;drawdown=0.
    for value in curve:
        high=max(high,value);drawdown=max(drawdown,1-value/high)
    final=previous_value
    if bars: flows.append((bars[-1].date,final))
    return {'strategy':mode,'contributions':contributions,'endingValue':round(final,2),'cash':round(cash,2),
      'timeWeightedReturn':round((curve[-1]-1)*100,4) if curve else 0,'maxDrawdown':round(drawdown*100,4),
      'xirr':xirr(flows),'transactions':transactions,'samples':len(bars),'cashflowCount':len(flows)-1,
      'assumptions':'研究示例；零股／小數單位、配息即時再投入、現金利息0、不執行賣出交易。費率與滑價為可調研究假設，非個人券商報價。'}


def run(asset):
    if asset not in {'2330','0050'}: raise ValueError('Portfolio backtest only supports non-leveraged Taiwan products')
    state=json.loads((ROOT/'data/history.json').read_text());record=state.get(asset,{})
    bars=deserialize(record.get('bars',[]))
    if len(bars)<650 or record.get('eventsReviewedThrough','')<bars[-1].date.isoformat():
        raise ValueError('至少650筆且公司行動已覆核的公開授權歷史才可產出研究回測')
    bars=adjust_bars(bars,record.get('events',[])); values=indicator_series(bars)
    signals={}; ma={}
    for i in range(399,len(bars)):
        scores=[score_at(bars,values,j) for j in range(i-2,i+1)]
        signals[bars[i].date.isoformat()]=all(s['qualifies'] for s in scores)
        ma[bars[i].date.isoformat()]=bars[i].close>values[i]['ma200']>values[i]['ma200Past']
    # Fixed rules, chronological holdout only. No optimization on the evaluation period.
    evaluation=bars[400:]
    report={'asset':asset,'start':evaluation[0].date.isoformat(),'end':evaluation[-1].date.isoformat(),'ruleVersion':'research-v1',
      'status':'research-only','note':'固定研究規則；此區段未用於參數最佳化。資料短於5年時不作長期優勢結論。',
      'results':[simulate(evaluation,{},'dca'),simulate(evaluation,signals,'signal'),simulate(evaluation,ma,'ma')]}
    write_json(ROOT/f'data/backtest-{asset}.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--id',required=True,choices=['2330','0050']);args=p.parse_args()
    try:
        r=run(args.id); print(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False))
    except ValueError as e: p.exit(2,str(e)+'\n')
