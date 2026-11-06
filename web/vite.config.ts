import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { readFile } from 'node:fs/promises';
export default defineConfig({
 plugins:[react(),{
  name:'private-research-preview',
  configureServer(server){
   if(process.env.RESEARCH_PREVIEW!=='true')return;
   server.middlewares.use(async(req,res,next)=>{
    if(req.url?.split('?')[0]!=='/data/markets.json')return next();
    try{
     const body=await readFile(new URL('../.private/markets.json',import.meta.url));
     res.statusCode=200;res.setHeader('Content-Type','application/json; charset=utf-8');res.setHeader('Cache-Control','no-store');res.end(body);
    }catch{res.statusCode=503;res.end('Private research snapshot not ready');}
   });
  }
 }],
 base:'./'
});
