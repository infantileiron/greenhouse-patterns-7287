import {list} from '../api/study';
import {useResource} from '../hooks/useResource';
export const useStudyStore=()=>useResource(list);
