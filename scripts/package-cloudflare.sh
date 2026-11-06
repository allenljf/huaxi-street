#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
npm --prefix web run build
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json
root=Path.cwd();assets=root/'web/dist';out=root/'output/huaxi-street-cloudflare.zip'
if not (assets/'index.html').exists():raise SystemExit('沒有index.html，請先完成建置')
snapshot=json.loads((assets/'data/markets.json').read_text())
if snapshot.get('privateResearch'):raise SystemExit('私人研究預覽不可經此入口意外發布')
out.parent.mkdir(exist_ok=True)
with ZipFile(out,'w',ZIP_DEFLATED) as archive:
    for path in sorted(assets.rglob('*')):
        if path.is_file():archive.write(path,path.relative_to(assets))
with ZipFile(out) as archive:
    assert 'index.html' in archive.namelist()
    assert all(not name.startswith(('.private/','.env','src/','node_modules/')) for name in archive.namelist())
print(f'Cloudflare上傳檔案：{out}')
print(f'快照時間：{snapshot["generatedAt"]}；標的數：{len(snapshot["markets"])}')
print('壓縮檔僅是此次快照；自動更新請使用 setup.sh --cloudflare。')
PY
