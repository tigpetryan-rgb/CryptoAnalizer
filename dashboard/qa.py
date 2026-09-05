from pathlib import Path
import json, re, sys

root = Path(__file__).resolve().parent
html = (root / 'index.html').read_text(encoding='utf-8')
snapshot = json.loads((root / 'snapshot.json').read_text(encoding='utf-8'))

errors=[]
def check(cond,msg):
    if not cond: errors.append(msg)

def nonneg_int(v):
    return isinstance(v,int) and not isinstance(v,bool) and v >= 0

check('<html lang="hy">' in html, 'HTML language must be Armenian')
check('Workstation' in html, 'Workstation marker missing')
check('ՎԵՐՋՆԱԿԱՆ PROTOCOL ՈՐՈՇՈՒՄ' in html, 'Final protocol decision area missing')
check('Public derivatives overlay' in html, 'Public overlay section missing')
check('NON-BINDING' in html, 'Public overlay non-binding label missing')
check('src="/style.css"' not in html and 'src="/app.js"' not in html and 'src="/data.js"' not in html, 'External local asset dependency detected')
check('gzip' not in html.lower() and 'decompressionstream' not in html.lower(), 'Loader/decompression bootstrap detected')
ids=re.findall(r'id="([^"]+)"',html)
check(len(ids)==len(set(ids)), 'Duplicate HTML ids detected')
for forbidden in ['data-page="home"','data-page="markets"','data-page="orders"','data-page="assets"']:
    check(forbidden not in html.lower(), f'Forbidden fake navigation returned: {forbidden}')

# Workstation 1.2+ must remain dual-source: a safe embedded fallback plus optional live snapshot sync.
if 'Workstation 1.2' in html:
    check('DASH_SNAPSHOT_URL' in html, 'v1.2 live snapshot URL missing')
    check('syncDashboardSnapshot' in html and 'applyDashboardSnapshot' in html, 'v1.2 snapshot sync functions missing')
    check('SNAPSHOT FALLBACK' in html and 'FALLBACK · SYNC ERROR' in html, 'v1.2 fallback state markers missing')
    check('window.DASH_DUE' in html, 'v1.2 dynamic due clock binding missing')
    check('cache:\'no-store\'' in html or 'cache:"no-store"' in html, 'v1.2 snapshot fetch must bypass stale cache')
    check('raw.githubusercontent.com/tigpetryan-rgb/CryptoAnalizer/main/dashboard/snapshot.json' in html, 'v1.2 canonical snapshot source mismatch')

check(snapshot.get('project_key')=='FUTURES_INTELLIGENCE','snapshot project key mismatch')
system=snapshot.get('system',{})
decision=snapshot.get('decision',{})
cap=snapshot.get('capabilities',{})
registries=snapshot.get('registries',{})
queue=system.get('queue',{})
check(str(system.get('state_revision','')).startswith('S'),'snapshot state revision invalid')
check(str(system.get('dispatch_revision','')).startswith('D'),'snapshot dispatch revision invalid')
for k in ['ready','claimed','done','cancelled','deadletter']:
    if k in queue: check(nonneg_int(queue[k]), f'queue.{k} must be a non-negative integer')
for k in ['current_actionable_setups','persisted_watchlist','active_trades']:
    if k in registries: check(nonneg_int(registries[k]), f'registries.{k} must be a non-negative integer')
check(snapshot.get('public_safety_overlay',{}).get('binding') is False,'public overlay must be non-binding')
check(bool(snapshot.get('rules',{}).get('hard_invalidation')),'hard invalidation rule missing')

auth=str(decision.get('authorization','')).upper()
check(bool(auth),'decision authorization missing')
w03=str(cap.get('W03','')).upper(); w04=str(cap.get('W04','')).upper(); w06=str(cap.get('W06','')).upper(); w07=str(cap.get('W07','')).upper()
stale_or_gated = any(token in (w03+' '+w04) for token in ['STALE','READY_REFRESH','WAITING']) or 'WAITING' in w06 or 'WAITING' in w07
if stale_or_gated:
    check(auth != 'AUTHORIZED','cannot authorize while W03/W04 are stale/refreshing or W06/W07 are gated')
if registries.get('current_actionable_setups') == 0:
    check(auth != 'AUTHORIZED','cannot authorize with zero current actionable setups')
if auth == 'AUTHORIZED':
    check(str(cap.get('W01','')).upper()=='DONE','authorized state requires W01 DONE')
    check(str(cap.get('W02','')).upper()=='DONE','authorized state requires W02 DONE')
    check(str(cap.get('W05','')).upper()=='DONE','authorized state requires W05 DONE')
    check(not any(token in w03 for token in ['STALE','READY_REFRESH','WAITING']),'authorized state requires fresh W03')
    check(not any(token in w04 for token in ['STALE','READY_REFRESH','WAITING']),'authorized state requires fresh W04')
    check('WAITING' not in w06 and 'REJECT' not in w06,'authorized state requires non-waiting/non-rejected W06')
    check('WAITING' not in w07 and 'FAIL' not in w07,'authorized state requires non-waiting/non-failed W07')
    check(registries.get('current_actionable_setups',0) >= 1,'authorized state requires at least one actionable setup')

if system.get('assignment_status') == 'READY':
    check(str(system.get('claim_owner','NONE')).upper() in ['NONE',''],'READY assignment must not have a claim owner')

for symbol,setup in snapshot.get('setups',{}).items():
    life=str(setup.get('lifecycle_state','')).upper()
    action=str(setup.get('action','')).upper()
    if 'VOID' in life or 'INVALIDATED' in life:
        check(('NO_ENTRY' in action) or ('NEW_THESIS_ONLY' in action) or ('NO_SETUP' in action), f'{symbol}: void/invalidated thesis must not expose an entry action')

lineage=snapshot.get('thesis_lineage')
if lineage is not None:
    required=set(lineage.get('required_fields',[]))
    must={'THESIS_ID','THESIS_STATUS','THESIS_GENERATION','SOURCE_W03_TIMESTAMP','SOURCE_STATE_REVISION','SUPERSEDES_THESIS_ID'}
    check(must.issubset(required),'thesis lineage required_fields incomplete')
    check('THESIS_ID' in str(lineage.get('chain_rule','')),'thesis lineage chain rule missing THESIS_ID binding')

scripts=re.findall(r'<script>(.*?)</script>',html,re.S)
check(bool(scripts),'inline JavaScript missing')
(root/'.qa-inline.js').write_text('\n'.join(scripts),encoding='utf-8')
if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'QA PASS: ids={len(ids)} scripts={len(scripts)} contract={snapshot.get("contract_version")} auth={auth}')
