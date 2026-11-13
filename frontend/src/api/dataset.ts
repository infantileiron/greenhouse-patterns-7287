import {request,post,download} from './client';
import type {Dataset, Sample} from '../types/domain';
export const list=()=>request<Dataset[]>('/datasets');
export const sampleRows=(id:string,offset=0)=>request<{rows:Sample[];total:number;dataset:Dataset}>(`/datasets/${id}/samples?offset=${offset}&limit=40`);
