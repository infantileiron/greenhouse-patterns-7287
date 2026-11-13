import {list} from '../api/report';
import {useResource} from '../hooks/useResource';
export const useReportStore=()=>useResource(list);
