import {list} from '../api/review';
import {useResource} from '../hooks/useResource';
export const useReviewStore=()=>useResource(list);
