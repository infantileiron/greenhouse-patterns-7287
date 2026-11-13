export const pct=(value:number)=>`${(value*100).toFixed(1)}%`;
export const num=(value:number)=>value.toLocaleString('zh-CN');
export const short=(id:string)=>id.startsWith('seed')?id:id.slice(0,8);
