import {request,post,download} from './client';
import type {Review} from '../types/domain';
export const list=()=>request<Review[]>('/reviews');
export const submitReview=(body:unknown)=>post<Review>('/reviews',body);
export const decideReview=(id:string,status:string)=>request<Review>(`/reviews/${id}`,{method:'PATCH',body:JSON.stringify({status})});
