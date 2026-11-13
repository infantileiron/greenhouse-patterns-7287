import {useCallback,useEffect,useState} from 'react';
export function useResource<T>(loader:()=>Promise<T[]>){
 const [data,setData]=useState<T[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const refresh=useCallback(async()=>{setLoading(true);try{setData(await loader());setError('')}catch(e){setError((e as Error).message)}finally{setLoading(false)}},[loader]);
 useEffect(()=>{void refresh()},[refresh]);return {data,loading,error,refresh};
}
