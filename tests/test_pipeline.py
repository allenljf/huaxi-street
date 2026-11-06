import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from market.pipeline import parse_date, expected_session, merge_bars, import_bundle, market_view, CATALOG
from market.engine import Bar


class PipelineTests(unittest.TestCase):
    def test_roc_dates_normalize(self):
        self.assertEqual(parse_date('115/11/05'),date(2026,11,5))
        self.assertEqual(parse_date('1151105'),date(2026,11,5))

    def test_monday_morning_uses_friday_and_respects_holidays(self):
        now=datetime(2026,11,9,8,tzinfo=ZoneInfo('Asia/Taipei'))
        self.assertEqual(expected_session(now,set()),date(2026,11,6))
        self.assertEqual(expected_session(now,{date(2026,11,6)}),date(2026,11,5))

    def test_same_session_replaces_rather_than_double_counts(self):
        a=Bar(date(2026,11,5),100,110,95,105)
        b=Bar(date(2026,11,5),100,111,95,106)
        self.assertEqual(merge_bars([a],[b],date(2026,11,5)),[b])

    def test_unfinished_future_bar_is_removed(self):
        b=Bar(date(2026,11,6),100,110,95,105)
        self.assertEqual(merge_bars([],[b],date(2026,11,5)),[])

    def test_import_requires_explicit_public_permission_and_source(self):
        with self.assertRaises(ValueError): import_bundle({'id':'0050','bars':[]})

    def test_official_daily_change_is_available_without_fake_history(self):
        b=Bar(date(2026,11,5),99.4,99.75,96.9,97.15)
        record={'quoteChange':{'date':'2026-11-05','value':-2.7}}
        result=market_view(CATALOG[2],[b],date(2026,11,5),record,None)
        self.assertAlmostEqual(result['changePct'],-2.70)
        self.assertIsNone(result['buyScore'])

    def test_stale_snapshot_keeps_prices_but_suppresses_action_scores(self):
        b=Bar(date(2026,11,4),100,110,95,105)
        result=market_view(CATALOG[0],[b],date(2026,11,5),{'reason':'short'},None)
        self.assertEqual(result['status'],'stale')
        self.assertEqual(result['close'],105)
        self.assertIsNone(result['buyScore'])

if __name__=='__main__': unittest.main()
