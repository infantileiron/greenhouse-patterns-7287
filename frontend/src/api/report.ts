import {request,post,download} from './client';
import type {Report} from '../types/domain';
export const list=()=>request<Report[]>('/reports');
export const downloadReport=(id:string)=>download(`/reports/${id}/download`,`nanling-review-${id}.csv`);
