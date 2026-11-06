import unittest
from datetime import date,datetime
from zoneinfo import ZoneInfo
from market.providers import parse_yahoo, parse_cnn, parse_vix

class ProviderTests(unittest.TestCase):
    def test_yahoo_keeps_only_closed_dates_and_adjusts_all_price_fields(self):
        stamps=[int(datetime(2026,11,d,9,30,tzinfo=ZoneInfo('America/New_York')).timestamp()) for d in [5,6]]
        payload={'chart':{'result':[{'timestamp':stamps,'meta':{'exchangeTimezoneName':'America/New_York'},'indicators':{'quote':[{'open':[100,110],'high':[102,115],'low':[99,109],'close':[100,112]}],'adjclose':[{'adjclose':[90,112]}]}}],'error':None}}
        record=parse_yahoo(payload,date(2026,11,5))
        self.assertEqual(len(record['bars']),1)
        self.assertEqual(record['bars'][0]['close'],90)
        self.assertAlmostEqual(record['bars'][0]['high'],91.8)
        self.assertEqual(record['quoteSnapshot']['close'],100)
        self.assertEqual(record['quoteSnapshot']['date'],'2026-11-05')

    def test_yahoo_missing_required_ohlc_is_not_invented(self):
        payload={'chart':{'result':[{'timestamp':[1793892600],'meta':{'exchangeTimezoneName':'America/New_York'},'indicators':{'quote':[{'open':[None],'high':[102],'low':[99],'close':[100]}],'adjclose':[{'adjclose':[100]}]}}]}}
        with self.assertRaises(ValueError):parse_yahoo(payload,date(2026,11,5))

    def test_cnn_bad_range_or_intraday_timestamp_not_published_as_closed(self):
        with self.assertRaises(ValueError):parse_cnn({'fear_and_greed':{'score':105,'timestamp':'2026-11-05T21:15:00Z'}},date(2026,11,5))
        with self.assertRaises(ValueError):parse_cnn({'fear_and_greed':{'score':20,'timestamp':'2026-11-06T15:00:00Z'}},date(2026,11,5))

    def test_cnn_accepts_post_close_snapshot_on_us_early_close(self):
        result=parse_cnn({'fear_and_greed':{'score':35,'timestamp':'2026-11-27T18:15:00Z'}},date(2026,11,27))
        self.assertEqual(result['value'],35)

    def test_vix_csv_stops_at_latest_completed_us_session(self):
        text='DATE,OPEN,HIGH,LOW,CLOSE\n11/05/2026,20,22,19,21\n11/06/2026,22,24,21,23\n'
        result=parse_vix(text,date(2026,11,5))
        self.assertEqual(result['value'],21)
        self.assertEqual(result['sessionDate'],'2026-11-05')

if __name__=='__main__':unittest.main()
