"""Completed regular sessions in exchange time, including DST and holidays."""
from datetime import datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo
import exchange_calendars as xcals
import pandas as pd

EXCHANGES={'tw':('XTAI','Asia/Taipei'),'us':('XNYS','America/New_York'),'jp':('XTKS','Asia/Tokyo'),'kr':('XKRX','Asia/Seoul')}
SCHEDULE_TEXT='亞洲 週一至五 16:00 · 美國 週二至六 08:00（台北時間）'

@lru_cache(maxsize=12)
def calendar(market,year):
    return xcals.get_calendar(EXCHANGES[market][0],start=f'{year-7}-01-01',end=f'{year+1}-12-31')


def last_completed_session(market,now,extra_holidays=frozenset()):
    if now.tzinfo is None: raise ValueError('now must be timezone aware')
    cal=calendar(market,now.year)
    stamp=pd.Timestamp(now).tz_convert('UTC')
    recent=cal.schedule.loc[str((now-timedelta(days=30)).date()):str(now.date())]
    days=recent.loc[recent['close']<=stamp].index
    days=[d.date() for d in days if d.date() not in extra_holidays]
    if not days: raise ValueError('No completed exchange session')
    return days[-1]


def market_key(asset):
    return 'us' if asset in {'sp500','nasdaq','vix','fear'} else 'jp' if asset=='nikkei' else 'kr' if asset=='kospi' else 'tw'


def selected_market(asset,batch):
    if batch not in {'asia','us','all'}: raise ValueError('Unknown market batch')
    return batch=='all' or (market_key(asset)=='us')==(batch=='us')


def batch_for_schedule(cron):
    return {'0 8 * * 1-5':'asia','0 0 * * 2-6':'us'}.get(cron,'all')


def next_update_at(asset,now):
    from datetime import time
    local=now.astimezone(ZoneInfo('Asia/Taipei'))
    us=market_key(asset)=='us';weekdays={1,2,3,4,5} if us else {0,1,2,3,4};hour=8 if us else 16
    for offset in range(8):
        day=local.date()+timedelta(days=offset)
        candidate=datetime.combine(day,time(hour),tzinfo=ZoneInfo('Asia/Taipei'))
        if day.weekday() in weekdays and candidate>local:return candidate.isoformat()
    raise ValueError('No next update')
