import {request,post,download} from './client';
import type {Study} from '../types/domain';
export const list=()=>request<Study[]>('/studies');
export const createStudy=(body:unknown)=>post<Study>('/studies',body);
