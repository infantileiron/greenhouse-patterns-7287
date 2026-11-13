export async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const token=sessionStorage.getItem('nanling-token');
 const response=await fetch(`/api${path}`,{...options,headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{}) ,...options.headers}});
 if(!response.ok){let detail:any;try{detail=(await response.json()).detail}catch{detail='服务暂不可用'};if(response.status===401){sessionStorage.removeItem('nanling-token');window.dispatchEvent(new Event('auth-expired'))};throw new Error(typeof detail==='string'?detail:JSON.stringify(detail))}
 return response.json();
}
export const post=<T>(path:string,body:unknown)=>request<T>(path,{method:'POST',body:JSON.stringify(body)});
export async function download(path:string,filename:string){
 const response=await fetch(`/api${path}`,{headers:{Authorization:`Bearer ${sessionStorage.getItem('nanling-token')}`}});
 if(!response.ok)throw new Error('下载失败，请确认报告已审批后重试');
 const url=URL.createObjectURL(await response.blob()); const a=document.createElement('a'); a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
