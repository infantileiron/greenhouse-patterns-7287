import {useEffect,useState} from 'react';
export function useRoute(){const [route,setRoute]=useState(location.hash.slice(1)||'overview');useEffect(()=>{const fn=()=>setRoute(location.hash.slice(1)||'overview');window.addEventListener('hashchange',fn);return()=>window.removeEventListener('hashchange',fn)},[]);return {route,navigate:(path:string)=>{location.hash=path}};}
