"""Execute the real wizard's stage2 in a sandbox with network commands replaced."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class SetupWizardTests(unittest.TestCase):
    def run_stage2(self,existing=False,remote_mismatch=False):
        script=(ROOT/'scripts/setup.sh').read_text()
        library=script.split('# STAGES: author this section.',1)[0]
        stage=script.split('stage "選擇專案網址"',1)[1].split('stage "確認亞洲與美國更新時段"',1)[0]
        # Only network/system boundaries are replaced. ask, confirm and write_env are real.
        shims='''
open_url() { :; }
gh() { if [[ "$1 $2" == "repo view" ]]; then return REPO_STATUS; fi; printf 'unexpected gh invocation' >&2; return 99; }
git() { if [[ "$1 $2 $3" == "remote get-url origin" ]]; then REMOTE_BODY; else return 0; fi; }
'''.replace('REPO_STATUS','0' if existing else '1').replace('REMOTE_BODY',"printf 'https://github.com/someone/other.git\\n'" if remote_mismatch else 'return 1')
        with tempfile.TemporaryDirectory() as folder:
            program=library+'\nENV_FILE="'+folder+'/.env"\n'+shims+stage
            result=subprocess.run([shutil.which('bash'),'-c',program],input='\nn\n',text=True,errors='replace',capture_output=True,cwd=folder,env={**os.environ,'LC_ALL':'en_US.UTF-8'},timeout=5)
            persisted=Path(folder,'.env').read_text()
        return result,persisted

    def test_declining_new_repo_confirmation_does_not_expand_chinese_punctuation_as_variable(self):
        result,persisted=self.run_stage2()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('建立公開GitHub專案 allenljf/huaxi-street？',result.stdout)
        self.assertIn('PROJECT_SLUG=huaxi-street',persisted)

    def test_existing_repo_message_handles_fullwidth_semicolon(self):
        result,_=self.run_stage2(existing=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('將使用既有專案：allenljf/huaxi-street；',result.stdout)

    def test_mismatched_origin_reports_error_and_stops_without_unbound_variable(self):
        result,_=self.run_stage2(remote_mismatch=True)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertIn('現有origin不是allenljf/huaxi-street；',result.stdout)
        self.assertNotIn('unbound variable',result.stderr)

    def test_cloudflare_confirmation_expands_names_without_eating_fullwidth_comma(self):
        script=(ROOT/'scripts/setup.sh').read_text()
        library=script.split('# STAGES: author this section.',1)[0]
        prompt=next(line for line in script.splitlines() if 'confirm "確認在Cloudflare帳號' in line)
        program=library+'\nCF_ACCOUNT_ID=account123; CF_PROJECT_NAME=huaxi-street; TARGET_REPO=allenljf/huaxi-street\n'+prompt
        result=subprocess.run([shutil.which('bash'),'-c',program],input='n\n',text=True,errors='replace',capture_output=True,env={**os.environ,'LC_ALL':'en_US.UTF-8'},timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Pages專案 huaxi-street，',result.stdout)
        self.assertIn('存入 allenljf/huaxi-street 的Actions Secrets？',result.stdout)

    def run_auth_step(self,script):
        library=script.split('# STAGES: author this section.',1)[0]
        auth=script.split('  step "完成建立並複製Token。不要貼到聊天裡。"',1)[1].split("  printf '%s'",1)[0]
        with tempfile.TemporaryDirectory() as folder:
            shims='''
CF_ACCOUNT_ID=account; CF_PROJECT_NAME=huaxi-street; TARGET_REPO=allenljf/huaxi-street
python3() {
  if [[ ! -f "CALL_FILE" ]]; then : > "CALL_FILE"; printf 'Cloudflare HTTP403\n' >&2; return 1; fi
  printf 'https://huaxi-street.pages.dev\n'
}
'''.replace('CALL_FILE',folder+'/attempted')
            program=library+shims+auth+'\nprintf "RESULT=%s\\n" "$CF_PAGES_URL"'
            return subprocess.run([shutil.which('bash'),'-c',program],input='first-token\ny\ny\nsecond-token\ny\n',text=True,errors='replace',capture_output=True,env={**os.environ,'LC_ALL':'en_US.UTF-8'},timeout=5)

    def test_failed_auth_can_retry_same_stage_without_exposing_tokens(self):
        result=self.run_auth_step((ROOT/'scripts/setup.sh').read_text())
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('RESULT=https://huaxi-street.pages.dev',result.stdout)
        self.assertIn('重新貼上Token',result.stdout)
        self.assertNotIn('first-token',result.stdout+result.stderr)
        self.assertNotIn('second-token',result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
