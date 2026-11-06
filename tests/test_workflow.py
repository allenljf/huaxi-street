import os,subprocess,sys,tempfile,textwrap,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class WorkflowTests(unittest.TestCase):
    def test_regional_selector_writes_real_github_env_record(self):
        text=(ROOT/'.github/workflows/daily-pages.yml').read_text()
        section=text.split('- name: Select regional batch',1)[1]
        script=textwrap.dedent(section.split("python - <<'PY'",1)[1].split('\n          PY',1)[0])
        for cron,want in [('0 8 * * 1-5','MARKET_BATCH=asia\n'),('0 0 * * 2-6','MARKET_BATCH=us\n')]:
            with self.subTest(cron=cron),tempfile.TemporaryDirectory() as folder:
                target=Path(folder)/'env'
                env={**os.environ,'EVENT_SCHEDULE':cron,'INPUT_BATCH':'','GITHUB_ENV':str(target)}
                subprocess.run([sys.executable,'-c',script],env=env,cwd=ROOT,check=True)
                self.assertEqual(target.read_text(),want)

if __name__=='__main__':unittest.main()
