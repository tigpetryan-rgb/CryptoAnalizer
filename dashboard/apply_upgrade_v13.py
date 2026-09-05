from pathlib import Path
import json
import subprocess

p=Path('dashboard/index.html')
s=p.read_text(encoding='utf-8')
index_changed=False

if 'Workstation 1.3' in s:
    print('dashboard renderer already at v1.3')
elif 'Workstation 1.2' not in s:
    raise RuntimeError('v1.2/v1.3 base marker missing')
else:
    s=s.replace('Workstation 1.2','Workstation 1.3')
    s=s.replace('const SETUPS={','const HISTORICAL_SETUPS={',1)
    anchor='};\nlet current=\'NEARUSDT\''
    if anchor not in s:
        raise RuntimeError('SETUPS closing anchor missing')
    s=s.replace(anchor,"};\nlet SETUPS={...HISTORICAL_SETUPS};\nlet current='NEARUSDT'",1)

    hydrate=r'''
function arrText(v,fallback='—'){if(Array.isArray(v))return v.length?v.join(' · '):fallback;if(v===undefined||v===null||v==='')return fallback;return String(v)}
function numOrNull(v){if(v===undefined||v===null||v==='')return null;let n=Number(v);return Number.isFinite(n)?n:null}
function thesisToSetup(t){
  const status=String(t.thesis_status||t.lifecycle_state||'PENDING').toUpperCase();
  const nonAction=['VOID','INVALIDATED','NO_SETUP','REJECTED'].some(x=>status.includes(x));
  const cls=nonAction?'red':(status.includes('READY')||status.includes('WAIT')||status.includes('TRIGGER')?'amber':'blue');
  const ann=t.chart_annotations||{};
  const sup=t.support||ann.support||ann.support_levels||[];
  const res=t.resistance||ann.resistance||ann.resistance_levels||[];
  const zone=t.entry_zone||ann.entry_zone||null;
  const source=[t.thesis_id,t.thesis_generation,t.source_w03_timestamp,t.source_state_revision].filter(Boolean).join(' · ');
  return {
    life:status,cls,isFreshProtocol:true,thesisId:t.thesis_id||'MISSING_THESIS_ID',
    label:`W03 · ${String(t.side||'').toUpperCase()} · ${status}`,
    oldState:status,
    entry:t.entry??ann.entry??'—',trigger:t.trigger??ann.trigger??'—',
    inv:numOrNull(t.invalidation??ann.invalidation),stop:numOrNull(t.stop??ann.stop),
    tp1:numOrNull(t.tp1??ann.tp1),tp2:numOrNull(t.tp2??ann.tp2),tp3:numOrNull(t.tp3??ann.tp3),
    zone:Array.isArray(zone)?zone.map(Number).filter(Number.isFinite):null,
    sup:Array.isArray(sup)?sup.map(Number).filter(Number.isFinite):[],
    res:Array.isArray(res)?res.map(Number).filter(Number.isFinite):[],
    thesis:`THESIS_ID ${t.thesis_id||'MISSING'} · ${arrText(t.thesis_generation,'—')} · source ${arrText(t.source_w03_timestamp,'—')} / ${arrText(t.source_state_revision,'—')}. ${arrText(t.thesis_summary||t.summary,'')}`.trim(),
    why:arrText(t.why||t.confluence_factors,'Protocol W03 thesis'),
    danger:arrText(t.why_not||t.contraindications||t.dangerous_flags,'—'),
    block:arrText(t.primary_blocker,'—'),
    confirm:arrText(t.required_confirmation,'—'),
    bull:arrText(t.scenarios?.bull||t.bull_scenario,'Fresh W03 structure only'),
    base:arrText(t.scenarios?.base||t.base_scenario,'WAIT until required confirmation'),
    bear:arrText(t.scenarios?.bear||t.bear_scenario,'Invalidation / alternate structure'),
    supersedes:t.supersedes_thesis_id||'NONE',source
  };
}
function hydrateProtocolSetups(d){
  const items=Array.isArray(d.current_theses)?d.current_theses:[];
  const dyn={};
  for(const t of items){if(!t||!t.symbol||!t.thesis_id)continue;dyn[String(t.symbol).toUpperCase()]=thesisToSetup(t)}
  SETUPS={...HISTORICAL_SETUPS,...dyn};
  const dynKeys=Object.keys(dyn);
  if(dynKeys.length){current=dynKeys.includes(current)?current:dynKeys[0]}
  else if(!SETUPS[current])current=Object.keys(SETUPS)[0];
  const active=document.querySelector('.activeNone b');
  if(active){active.textContent=dynKeys.length?`FRESH W03 THESES = ${dynKeys.length}`:'CURRENT ACTIONABLE SETUP = NONE'}
  if(document.getElementById('setups')?.classList.contains('on')&&SETUPS[current])renderSetup(current);
}
'''
    anchor2='function applyDashboardSnapshot(d){'
    if anchor2 not in s:
        raise RuntimeError('snapshot apply anchor missing')
    s=s.replace(anchor2,hydrate+'\n'+anchor2,1)

    call_anchor="  const sync=document.getElementById('syncState');if(sync){sync.textContent='SNAPSHOT LIVE';sync.className='tag green'}"
    if call_anchor not in s:
        raise RuntimeError('snapshot apply tail anchor missing')
    s=s.replace(call_anchor,"  hydrateProtocolSetups(d);\n"+call_anchor,1)

    old="setHtml('levels',[['Old Trigger',o.trigger],['Old Entry',o.entry],['Invalidation',fmt(o.inv)],['Stop Loss',fmt(o.stop)],['TP1',fmt(o.tp1)],['TP2',fmt(o.tp2)],['TP3',fmt(o.tp3)]]"
    new="let pref=o.isFreshProtocol?'':'Old ';setHtml('levels',[[pref+'Trigger',o.trigger],[pref+'Entry',o.entry],['Invalidation',fmt(o.inv)],['Stop Loss',fmt(o.stop)],['TP1',fmt(o.tp1)],['TP2',fmt(o.tp2)],['TP3',fmt(o.tp3)]]"
    if old not in s:
        raise RuntimeError('levels render anchor missing')
    s=s.replace(old,new,1)

    p.write_text(s,encoding='utf-8')
    index_changed=True
    print('dashboard upgraded to v1.3 thesis-aware renderer')

# Presentation-contract reconciliation only. Do not alter protocol/market state.
sp=Path('dashboard/snapshot.json')
d=json.loads(sp.read_text(encoding='utf-8'))
meta=d.setdefault('meta',{})
meta['dashboard_version']='Analyst Workstation 1.3'
source_commit=subprocess.check_output(
    ['git','log','-1','--format=%H','--','dashboard/index.html'],
    text=True
).strip()
if len(source_commit)==40:
    meta['dashboard_source_commit']=source_commit
if 'current_theses' not in d:
    d['current_theses']=[]
sp.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'v1.3 metadata reconciled; index_changed={index_changed}; source_commit={source_commit}')
