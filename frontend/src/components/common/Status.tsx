import {RunStatus,ReviewStatus} from '../../constants/enums';
export function Status({value}:{value:string}){return <span className={`status ${value}`}><i/>{({...RunStatus,...ReviewStatus} as Record<string,string>)[value]||value}</span>}
