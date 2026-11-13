import { defineConfig } from 'vite';
export default defineConfig({server:{port:18204,proxy:{'/api':{target:'http://127.0.0.1:19204',rewrite:(path)=>path.replace(/^\/api/,'')}}}});
