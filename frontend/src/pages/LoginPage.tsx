import {useState} from 'react';
import {post} from '../api/client';
import type {User} from '../types/domain';
import {Specimen} from '../components/common/Specimen';
export function LoginPage({onLogin}:{onLogin:(user:User)=>void}){
 const [email,setEmail]=useState('analyst@nanling.test'),[password,setPassword]=useState('Nanling!2611'),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);try{const data=await post<{token:string;user:User}>('/auth/login',{email,password});sessionStorage.setItem('nanling-token',data.token);onLogin(data.user)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <main className="login"><section className="login-art"><span className="eyebrow">NANLING / FIELD NOTES 2026</span><h1>从病征的共现，<br/>寻找复查的线索。</h1><Specimen/><p>南岭育苗研究站 · 8 个温室 / 16 位研究人员<br/>让每一条关联，都经得起样本与统计的检验。</p></section><section className="login-form"><span className="eyebrow">研究员入口 / 01</span><h2>打开温室档案</h2><p>病征组合筛查与独立复查工作台</p><form onSubmit={submit}><label>邮箱<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label>密码<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required/></label>{error&&<p role="alert" className="error">{error}</p>}<button className="primary" disabled={busy}>{busy?'核验身份中…':'进入研究档案 →'}</button></form><div className="login-accounts"><b>模拟研究账号</b><p>admin / analyst / viewer @nanling.test</p><p>统一密码：Nanling!2611</p><small>管理员审批 · 农艺师研究 · 观察员只读</small></div></section></main>
}
