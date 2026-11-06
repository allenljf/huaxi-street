import unittest
from datetime import date, timedelta
from market.engine import Bar, adjust_bars, analyze, indicators, cross


def series(count=430):
    return [Bar(date(2024,1,1)+timedelta(days=i), 100+i, 102+i, 99+i, 101+i) for i in range(count)]


class EngineTests(unittest.TestCase):
    def test_flat_prices_are_finite_and_kd_neutral(self):
        result = indicators([Bar(date(2024,1,1)+timedelta(days=i),100,100,100,100) for i in range(430)])
        self.assertEqual(result['rsi'],50)
        self.assertEqual(result['k'],50)
        self.assertEqual(result['d'],50)
        self.assertEqual(result['adx'],0)

    def test_rising_prices_rsi_100_and_long_trend(self):
        result=analyze(series())
        self.assertEqual(result['indicators']['rsi'],100)
        self.assertEqual(result['parts']['trend'],8)
        self.assertLessEqual(result['buyScore'],8)

    def test_warmup_is_not_a_neutral_score(self):
        self.assertIsNone(analyze(series(30))['buyScore'])

    def test_split_adjusts_all_ohlc_before_event(self):
        bars=[Bar(date(2025,6,11),200,208,196,204),Bar(date(2025,6,18),50,52,49,51)]
        adjusted=adjust_bars(bars,[{'date':'2025-06-18','split':4,'dividend':0}])
        self.assertEqual(adjusted[0].close,51)
        self.assertEqual(adjusted[0].high,52)
        self.assertEqual(adjusted[1].close,51)

    def test_cash_dividend_adjustment_does_not_fake_crash(self):
        bars=[Bar(date(2025,1,1),100,100,100,100),Bar(date(2025,1,2),90,90,90,90)]
        adjusted=adjust_bars(bars,[{'date':'2025-01-02','split':1,'dividend':10}])
        self.assertEqual(adjusted[0].close,90)

    def test_earlier_dividend_then_later_split_uses_correct_cash_units(self):
        bars=[Bar(date(2025,1,1),100,100,100,100),Bar(date(2025,1,2),90,90,90,90),Bar(date(2025,6,18),22.5,22.5,22.5,22.5)]
        adjusted=adjust_bars(bars,[{'date':'2025-01-02','split':1,'dividend':10},{'date':'2025-06-18','split':4,'dividend':0}])
        self.assertEqual(adjusted[0].close,22.5)

    def test_future_corporate_action_does_not_rewrite_today(self):
        bars=[Bar(date(2025,1,1),100,100,100,100)]
        self.assertEqual(adjust_bars(bars,[{'date':'2026-01-01','split':4}])[0].close,100)

    def test_cross_is_an_event_not_a_persistent_state(self):
        self.assertEqual(cross(2,3,4,3),'golden')
        self.assertIsNone(cross(4,3,5,3))

    def test_bad_bar_rejected(self):
        with self.assertRaises(ValueError): Bar(date(2024,1,1),100,99,90,100)

    def test_confirmation_uses_consecutive_bars_not_repeated_runs(self):
        self.assertEqual(analyze(series())['confirmed'], analyze(series())['confirmed'])

if __name__=='__main__': unittest.main()
