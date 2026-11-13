import {list} from '../api/dataset';
import {useResource} from '../hooks/useResource';
export const useDatasetStore=()=>useResource(list);
