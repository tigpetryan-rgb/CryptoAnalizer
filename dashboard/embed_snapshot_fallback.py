from pathlib import Path
import json

INDEX = Path('dashboard/index.html')
SNAPSHOT = Path('dashboard/snapshot.json')

html = INDEX.read_text(encoding='utf-8')
snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
if snapshot.get('project_key') != 'FUTURES_INTELLIGENCE':
    raise RuntimeError('snapshot project mismatch')

payload = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'))
url_line = "const DASH_SNAPSHOT_URL='https://raw.githubusercontent.com/tigpetryan-rgb/CryptoAnalizer/main/dashboard/snapshot.json';"
embedded_prefix = 'const DASH_EMBEDDED_SNAPSHOT='
embedded_line = embedded_prefix + payload + ';'

if url_line not in html:
    raise RuntimeError('DASH_SNAPSHOT_URL anchor missing')

if embedded_prefix in html:
    lines = html.splitlines()
    replaced = False
    for i, line in enumerate(lines):
        if line.startswith(embedded_prefix):
            lines[i] = embedded_line
            replaced = True
            break
    if not replaced:
        raise RuntimeError('embedded snapshot line could not be replaced')
    html = '\n'.join(lines)
    if INDEX.read_text(encoding='utf-8').endswith('\n'):
        html += '\n'
else:
    html = html.replace(url_line, url_line + '\n' + embedded_line, 1)

old_sync = """async function syncDashboardSnapshot(){
  const sync=document.getElementById('syncState');
  try{const r=await fetch(DASH_SNAPSHOT_URL+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const d=await r.json();applyDashboardSnapshot(d)}
  catch(e){if(sync){sync.textContent='FALLBACK · SYNC ERROR';sync.className='tag amber'};console.warn('dashboard snapshot fallback active',e)}
}"""

new_sync = """async function syncDashboardSnapshot(){
  const sync=document.getElementById('syncState');
  let embeddedOk=false;
  try{applyDashboardSnapshot(DASH_EMBEDDED_SNAPSHOT);embeddedOk=true;if(sync){sync.textContent='SNAPSHOT EMBEDDED';sync.className='tag green'}}
  catch(e){console.error('embedded authoritative snapshot invalid',e)}
  try{const r=await fetch(DASH_SNAPSHOT_URL+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const d=await r.json();applyDashboardSnapshot(d)}
  catch(e){if(sync){sync.textContent=embeddedOk?'EMBEDDED SAFE · SYNC ERROR':'FALLBACK · SYNC ERROR';sync.className=embeddedOk?'tag green':'tag amber'};console.warn('remote dashboard snapshot unavailable; embedded snapshot retained',e)}
}"""

if 'let embeddedOk=false;' not in html:
    if old_sync not in html:
        raise RuntimeError('syncDashboardSnapshot anchor missing')
    html = html.replace(old_sync, new_sync, 1)

INDEX.write_text(html, encoding='utf-8')
print(f"embedded authoritative snapshot {snapshot.get('system',{}).get('state_revision')} / {snapshot.get('system',{}).get('dispatch_revision')}")
