from pathlib import Path

p = Path('dashboard/index.html')
s = p.read_text(encoding='utf-8')
if 'Workstation 1.2' in s:
    print('dashboard already at v1.2; no change')
    raise SystemExit(0)
if 'Workstation 1.1' not in s:
    raise RuntimeError('v1.1 base marker missing')

s = s.replace('S000033 / D000014 · Workstation 1.1', 'S000034 / D000014 · Workstation 1.2', 1)
s = s.replace('<span class="tag amber">H02 REFRESH PENDING</span>', '<span class="tag amber">H02 REFRESH PENDING</span> <span id="syncState" class="tag">SNAPSHOT FALLBACK</span>', 1)
s = s.replace('id="dueState">23:00 +04:00', 'id="dueState">23:55 +04:00', 1)
s = s.replace("Date.parse('2026-09-05T23:00:00+04:00')", "Date.parse(window.DASH_DUE||'2026-09-05T23:55:00+04:00')", 1)
s = s.replace('2026-09-05 23:00 +04:00</small></div><span class="amber">PENDING</span>', '2026-09-05 23:55 +04:00</small></div><span class="amber">RECOVERED READY</span>', 1)

sync_js = r'''
window.DASH_DUE='2026-09-05T23:55:00+04:00';
const DASH_SNAPSHOT_URL='https://raw.githubusercontent.com/tigpetryan-rgb/CryptoAnalizer/main/dashboard/snapshot.json';
function dashText(el,v){if(el&&v!==undefined&&v!==null)el.textContent=String(v)}
function dashMetric(label){return [...document.querySelectorAll('.k')].find(x=>x.querySelector('small')?.textContent.trim()===label)}
function dashRow(label){return [...document.querySelectorAll('.row')].find(x=>x.querySelector('b')?.textContent.trim()===label)}
function dashStep(id){return [...document.querySelectorAll('.step')].find(x=>x.querySelector('b')?.textContent.trim()===id)}
function applyDashboardSnapshot(d){
  if(!d||d.project_key!=='FUTURES_INTELLIGENCE')throw new Error('snapshot project mismatch');
  const sys=d.system||{},dec=d.decision||{},cap=d.capabilities||{},reg=d.registries||{},q=sys.queue||{};
  const head=document.querySelector('.brand')?.parentElement?.querySelector('small');
  if(head)head.textContent=`Cycle ${sys.cycle_id||'—'} · ${sys.state_revision||'—'} / ${sys.dispatch_revision||'—'} · Workstation 1.2`;
  const hero=document.querySelector('.hero');
  dashText(hero?.querySelector('h1'),dec.status||'WAIT / NO TRADE');
  const authTag=hero?.querySelector('.tag.red'); if(authTag)authTag.textContent=dec.authorization||'NOT AUTHORIZED';
  const heroP=hero?.querySelector('p'); if(heroP&&dec.reason)heroP.textContent=dec.reason;
  let m=dashMetric('Current actionable setups'); if(m)dashText(m.querySelector('b'),reg.current_actionable_setups??0);
  m=dashMetric('Watchlist / Active'); if(m)dashText(m.querySelector('b'),`${reg.persisted_watchlist??0} / ${reg.active_trades??0}`);
  const active=dashRow('Active assignment'); if(active){dashText(active.querySelector('small'),sys.active_assignment||'NONE');dashText(active.querySelector('span'),sys.assignment_status||'—')}
  const due=dashRow('Due'); if(due){const ds=due.querySelector('small');if(ds&&sys.assignment_due_at){let t=new Date(sys.assignment_due_at);ds.textContent=new Intl.DateTimeFormat('hy-AM',{timeZone:'Asia/Yerevan',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(t)+' +04:00'}dashText(due.querySelector('span'),sys.assignment_status==='READY'?'READY':'—')}
  if(sys.assignment_due_at)window.DASH_DUE=sys.assignment_due_at;
  const dueState=document.getElementById('dueState');if(dueState&&sys.assignment_due_at){let t=new Date(sys.assignment_due_at);dueState.textContent=new Intl.DateTimeFormat('hy-AM',{timeZone:'Asia/Yerevan',hour:'2-digit',minute:'2-digit',hour12:false}).format(t)+' +04:00'}
  const labels={Ready:q.ready,Claimed:q.claimed,Done:q.done,Cancelled:q.cancelled};for(const [k,v] of Object.entries(labels)){let x=dashMetric(k);if(x&&v!==undefined)dashText(x.querySelector('b'),v)}
  for(const id of ['W01','W02','W03','W04','W05','W06','W07']){let st=dashStep(id);if(st&&cap[id]){dashText(st.querySelector('small'),cap[id]);st.classList.remove('done','current','block');let v=String(cap[id]).toUpperCase();if(v==='DONE'||v.includes('PASS')||v.includes('APPROVE'))st.classList.add('done');else if(v.includes('READY')||v.includes('REFRESH'))st.classList.add('current');else if(v.includes('REJECT')||v.includes('FAIL'))st.classList.add('block')}}
  const none=document.querySelector('.activeNone b');if(none)none.textContent=(reg.current_actionable_setups||0)>0?`CURRENT ACTIONABLE SETUPS = ${reg.current_actionable_setups}`:'CURRENT ACTIONABLE SETUP = NONE';
  const sync=document.getElementById('syncState');if(sync){sync.textContent='SNAPSHOT LIVE';sync.className='tag green'}
  document.documentElement.dataset.snapshotRevision=sys.state_revision||'';
}
async function syncDashboardSnapshot(){
  const sync=document.getElementById('syncState');
  try{const r=await fetch(DASH_SNAPSHOT_URL+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const d=await r.json();applyDashboardSnapshot(d)}
  catch(e){if(sync){sync.textContent='FALLBACK · SYNC ERROR';sync.className='tag amber'};console.warn('dashboard snapshot fallback active',e)}
}
syncDashboardSnapshot();setInterval(syncDashboardSnapshot,60000);
'''
anchor='function fmtAge(ms)'
if anchor not in s:
    raise RuntimeError('freshness JS anchor missing')
s=s.replace(anchor,sync_js+'\n'+anchor,1)

p.write_text(s,encoding='utf-8')
print('dashboard upgraded to v1.2 dual-source snapshot sync')
