from pathlib import Path
import json, re, sys

root = Path(__file__).resolve().parent
html = (root / 'index.html').read_text(encoding='utf-8')
snapshot = json.loads((root / 'snapshot.json').read_text(encoding='utf-8'))

errors=[]
def check(cond,msg):
    if not cond: errors.append(msg)

check('<html lang="hy">' in html, 'HTML language must be Armenian')
check('Workstation 1.1' in html, 'Expected Workstation 1.1 marker missing')
check('WAIT / NO TRADE' in html and 'NOT AUTHORIZED' in html, 'Safety decision guard missing')
check('CURRENT ACTIONABLE SETUP = NONE' in html, 'Actionable-setup safety guard missing')
check('Public derivatives overlay' in html, 'Public overlay section missing')
check('NON-BINDING' in html, 'Public overlay non-binding label missing')
check('H02-A06' in html, 'Current assignment reference missing')
check('src="/style.css"' not in html and 'src="/app.js"' not in html and 'src="/data.js"' not in html, 'External local asset dependency detected')
check('gzip' not in html.lower() and 'decompressionstream' not in html.lower(), 'Loader/decompression bootstrap detected')
ids=re.findall(r'id="([^"]+)"',html)
check(len(ids)==len(set(ids)), 'Duplicate HTML ids detected')
for forbidden in ['data-page="home"','data-page="markets"','data-page="orders"','data-page="assets"']:
    check(forbidden not in html.lower(), f'Forbidden fake navigation returned: {forbidden}')
check(snapshot.get('project_key')=='FUTURES_INTELLIGENCE','snapshot project key mismatch')
check(snapshot.get('system',{}).get('state_revision','').startswith('S'),'snapshot state revision invalid')
check(snapshot.get('decision',{}).get('authorization')=='NOT AUTHORIZED','snapshot authorization guard invalid')
check(snapshot.get('registries',{}).get('active_trades')==0,'unexpected active trade registry')
check(snapshot.get('registries',{}).get('persisted_watchlist')==0,'unexpected persisted watchlist registry')
check(snapshot.get('public_safety_overlay',{}).get('binding') is False,'public overlay must be non-binding')
check(snapshot.get('rules',{}).get('hard_invalidation'),'hard invalidation rule missing')

scripts=re.findall(r'<script>(.*?)</script>',html,re.S)
check(bool(scripts),'inline JavaScript missing')
(root/'.qa-inline.js').write_text('\n'.join(scripts),encoding='utf-8')
if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'QA PASS: ids={len(ids)} scripts={len(scripts)} contract={snapshot.get("contract_version")}')
