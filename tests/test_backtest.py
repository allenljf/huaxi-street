import unittest
from datetime import date,timedelta
from market.engine import Bar
from market.backtest import simulate, xirr

class BacktestTests(unittest.TestCase):
    def test_fixed_deposit_does_not_create_a_return_in_flat_market(self):
        bars=[Bar(date(2026,1,1)+timedelta(days=i),100,100,100,100) for i in range(120)]
        report=simulate(bars,{},'dca',fee_rate=0,slippage=0)
        self.assertEqual(report['contributions'],40000)
        self.assertEqual(report['endingValue'],40000)
        self.assertAlmostEqual(report['timeWeightedReturn'],0)
        self.assertAlmostEqual(report['maxDrawdown'],0)

    def test_signal_from_today_cannot_execute_at_todays_open(self):
        bars=[Bar(date(2026,1,5),100,100,100,100),Bar(date(2026,1,6),110,110,110,110)]
        report=simulate(bars,{'2026-01-05':True},'signal',fee_rate=0,slippage=0)
        self.assertEqual(report['transactions'][0]['budget'],8000)
        self.assertEqual(report['cash'],2000)

    def test_force_invest_after_three_months_preserves_same_budget(self):
        bars=[Bar(date(2026,1,1)+timedelta(days=i),100,100,100,100) for i in range(130)]
        report=simulate(bars,{},'signal',fee_rate=0,slippage=0)
        self.assertEqual(report['contributions'],50000)
        self.assertLess(report['cash'],10000)
        self.assertEqual(report['endingValue'],50000)

    def test_zero_fee_does_not_silently_remove_explicit_slippage(self):
        bars=[Bar(date(2026,1,1),100,100,100,100)]
        report=simulate(bars,{},'dca',fee_rate=0,slippage=.1)
        self.assertAlmostEqual(report['endingValue'],9090.91)

    def test_xirr_hand_checked_one_year(self):
        self.assertAlmostEqual(xirr([(date(2025,1,1),-100),(date(2026,1,1),110)]),.1,places=6)

if __name__=='__main__': unittest.main()
