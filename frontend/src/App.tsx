import {useEffect,useState} from 'react';
import {request} from './api/client';
import {useDatasetStore} from './stores/dataset';
import {useStudyStore} from './stores/study';
import {useRunStore} from './stores/run';
import {useReviewStore} from './stores/review';
import {useReportStore} from './stores/report';
import type {User,Workspace} from './types/domain';
import {Roles} from './constants/enums';
import {routes} from './router/routes';
import {useRoute} from './hooks/useRoute';
import {LoginPage} from './pages/LoginPage';
import {OverviewPage} from './pages/OverviewPage';
import {DatasetsPage} from './pages/DatasetsPage';
import {StudiesPage} from './pages/StudiesPage';
import {ResultsPage} from './pages/ResultsPage';
import {ReviewsPage} from './pages/ReviewsPage';
function StudyWorkspace({user,onLogout}:{user:User;onLogout:()=>void}){
 const datasets=useDatasetStore(),studies=useStudyStore(),runs=useRunStore(),reviews=useReviewStore(),reports=useReportStore();
 const {route,navigate}=useRoute();const [selectedRun,selectRun]=useState('');
 const workspace:Workspace={user,datasets,studies,runs,reviews,reports,navigate,selectedRun,selectRun};
 const Pages:Record<string,React.ComponentType<Workspace>>={overview:OverviewPage,datasets:DatasetsPage,studies:StudiesPage,results:ResultsPage,reviews:ReviewsPage};const Page=Pages[route]||OverviewPage;
 return <div className="app-shell"><aside className="sidebar"><a className="brand" href="#overview"><span>南岭温室</span><small>NANLING HERBARIUM</small></a><p className="sidebar-note">病征组合筛查<br/>FIELD RESEARCH / 2026</p><nav>{routes.map(r=><a key={r.path} className={route===r.path?'active':''} href={`#${r.path}`}><span>{r.number}</span>{r.label}<i>↗</i></a>)}</nav><div className="sidebar-footer"><span className="seal">NL</span><p>模拟研究 · 8个温室<br/>关联不等于因果</p><b>{user.name}</b><small>{Roles[user.role]}</small><button onClick={onLogout}>退出档案</button></div></aside><main className="workspace"><div className="topline"><span>南岭育苗研究站 / 植物病征观察</span><span className="mono">NOV 2026 · EXPLORATORY</span></div><Page {...workspace}/><footer>NL / RESEARCH ARCHIVE <span>记录样本 · 量化证据 · 独立复查</span></footer></main></div>
}
export default function App(){
 const [user,setUser]=useState<User|null>(null),[checking,setChecking]=useState(!!sessionStorage.getItem('nanling-token'));
 useEffect(()=>{if(sessionStorage.getItem('nanling-token'))request<User>('/auth/me').then(setUser).catch(()=>sessionStorage.removeItem('nanling-token')).finally(()=>setChecking(false));const clear=()=>setUser(null);window.addEventListener('auth-expired',clear);return()=>window.removeEventListener('auth-expired',clear)},[]);
 if(checking)return <p className="notice">正在核验研究身份…</p>;
 return user?<StudyWorkspace user={user} onLogout={()=>{sessionStorage.removeItem('nanling-token');setUser(null)}}/>:<LoginPage onLogin={setUser}/>;
}
