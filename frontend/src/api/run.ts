import {request,post,download} from './client';
import type {Run} from '../types/domain';
export const list=()=>request<Run[]>('/runs');
export const runDetail=(id:string)=>request<Run>(`/runs/${id}`);
export const createRun=(study_id:string)=>post<Run>('/runs',{study_id});
