import {useState} from 'react';
import type {Workspace,Rule} from '../types/domain';
import {decideReview} from '../api/review';
import {downloadReport} from '../api/report';
import {RuleTable} from '../components/common/RuleTable';
import {runDetail} from '../api/run';
import {Status} from '../components/common/Status';
import {State} from '../components/common/State';
export function ReviewsPage(w:Workspace){
 const [error,setError]=useState(''),[busy,setBusy]=useState(''),[preview,setPreview]=useState<Rule[]>([]);
 async function decide(id:string,status:string){setBusy(id);try{await decideReview(id,status);await Promise.all([w.reviews.refresh(),w.reports.refresh()])}catch(e){setError((e as Error).message)}finally{setBusy('')}}
 async function inspect(runId:string,ids:string[]){try{const run=await runDetail(runId);setPreview(run.result?.rules.filter(r=>ids.includes(r.rule_id))||[])}catch(e){setError((e as Error).message)}}
 return <><header className="compact-heading"><span className="eyebrow">INDEPENDENT CHECK / 05</span><h1>关联之后，回到温室</h1><p>农艺师提出复查规则，站长批准后生成可下载清单。</p></header><State error={error||w.reviews.error} onRetry={w.reviews.refresh}/><section className="split"><div><h2>复查申请</h2>{w.reviews.data.map(r=><article className="review-entry" key={r.id}><div className="toolbar"><b>{r.rule_ids.length} 条规则 / {r.id.slice(0,12)}</b><Status value={r.status}/></div><p>{r.note}</p><small>{r.submitted_by}{r.reviewed_by&&` → ${r.reviewed_by}`}</small><div className="actions"><button onClick={()=>inspect(r.run_id,r.rule_ids)}>查看规则证据</button>{r.status==='pending'&&w.user.role==='admin'&&<><button disabled={!!busy} onClick={()=>decide(r.id,'approved')}>批准并生成清单</button><button disabled={!!busy} onClick={()=>decide(r.id,'rejected')}>退回</button></>}</div></article>)}</div><aside className="report-shelf"><span className="eyebrow">APPROVED EXPORTS</span><h2>复查清单</h2><State empty={!w.reports.data.length}/>{w.reports.data.map(r=><article key={r.id}><span className="mono">CSV / UTF-8</span><h3>{r.name}</h3><p>支持数、分母、置信度、提升度、p/q值、样本校验和及说明</p><button onClick={()=>downloadReport(r.id).catch(e=>setError(e.message))}>下载清单 ↓</button></article>)}<p className="muted">仅包含站长批准的规则；模拟数据不能直接用于农事决策。</p></aside></section>{!!preview.length&&<section><h2>复查证据</h2><RuleTable rules={preview}/></section>}</>
}
