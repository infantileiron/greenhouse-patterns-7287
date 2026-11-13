import {list} from '../api/run';
import {useResource} from '../hooks/useResource';
export const useRunStore=()=>useResource(list);
