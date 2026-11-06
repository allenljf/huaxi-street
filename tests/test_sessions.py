import unittest
from datetime import datetime,date
from zoneinfo import ZoneInfo
from market.sessions import last_completed_session, batch_for_schedule, selected_market, next_update_at

class SessionTests(unittest.TestCase):
    def test_friday_asia_at_1600_has_same_day_close(self):
        now=datetime(2026,11,6,16,tzinfo=ZoneInfo('Asia/Taipei'))
        for market in ['tw','jp','kr']:
            self.assertEqual(last_completed_session(market,now),date(2026,11,6))

    def test_taiwan_before_close_does_not_use_unfinished_day(self):
        now=datetime(2026,11,6,13,29,tzinfo=ZoneInfo('Asia/Taipei'))
        self.assertEqual(last_completed_session('tw',now),date(2026,11,5))

    def test_saturday_0800_includes_us_friday(self):
        now=datetime(2026,11,7,8,tzinfo=ZoneInfo('Asia/Taipei'))
        self.assertEqual(last_completed_session('us',now),date(2026,11,6))

    def test_thanksgiving_does_not_look_for_nonexistent_thursday_bar(self):
        now=datetime(2026,11,27,8,tzinfo=ZoneInfo('Asia/Taipei'))
        self.assertEqual(last_completed_session('us',now),date(2026,11,25))

    def test_us_summer_time_is_resolved_in_new_york_zone(self):
        now=datetime(2026,7,7,8,tzinfo=ZoneInfo('Asia/Taipei'))
        self.assertEqual(last_completed_session('us',now),date(2026,7,6))

    def test_next_regional_update_keeps_us_friday_and_asian_weekend_distinct(self):
        now=datetime(2026,11,6,18,tzinfo=ZoneInfo('Asia/Taipei'))
        self.assertEqual(next_update_at('0050',now),'2026-11-09T16:00:00+08:00')
        self.assertEqual(next_update_at('sp500',now),'2026-11-07T08:00:00+08:00')

    def test_batches_have_exact_utc_cron_and_independent_membership(self):
        self.assertEqual(batch_for_schedule('0 8 * * 1-5'),'asia')
        self.assertEqual(batch_for_schedule('0 0 * * 2-6'),'us')
        self.assertTrue(selected_market('nikkei','asia'))
        self.assertFalse(selected_market('sp500','asia'))
        self.assertTrue(selected_market('sp500','us'))
        self.assertFalse(selected_market('0050','us'))

if __name__=='__main__':unittest.main()
