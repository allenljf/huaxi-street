import json,tempfile,unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
from market import pipeline

class BatchTests(unittest.TestCase):
    def test_asia_update_does_not_refresh_or_overwrite_us_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'.private').mkdir()
            old={'sp500':{'bars':[{'date':'2026-11-05','open':100,'high':100,'low':100,'close':100}], 'lastSuccessfulFetchAt':'2026-11-06T08:00:00+08:00'}}
            (root/'.private/research-history.json').write_text(json.dumps(old))
            def fetched(asset,cutoff):
                self.assertNotIn(asset,{'sp500','nasdaq'})
                return {'bars':[{'date':'2026-11-06','open':200,'high':200,'low':200,'close':200}], 'priceBasis':'vendor-adjusted'}
            with patch.object(pipeline,'ROOT',root),patch.object(pipeline,'fetch_yahoo',side_effect=fetched):
                data=pipeline.build(now=datetime(2026,11,6,16,tzinfo=ZoneInfo('Asia/Taipei')),batch='asia',research=True)
            updated=json.loads((root/'.private/research-history.json').read_text())
            self.assertEqual(updated['sp500'],old['sp500'])
            self.assertEqual(next(m for m in data['markets'] if m['id']=='sp500')['lastSuccessfulFetchAt'],'2026-11-06T08:00:00+08:00')
            self.assertFalse((root/'web/public/data/markets.json').exists())

if __name__=='__main__':unittest.main()
