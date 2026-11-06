export interface Indicator { name:string; value:string; buyScore:number|null; sellScore:number|null }
export interface MarketView {
 id:string; name:string; en:string; symbol:string; region:'tw'|'us'|'asia'; kind:string;
 sessionDate:string|null; close:number|null; changePct:number|null; sparkline:number[];
 history:{date:string;close:number}[]; buyScore:number|null; sellScore:number|null;
 status:'fresh'|'holiday'|'stale'|'unavailable'; scoreStatus:string; confirmed:boolean; leveraged:boolean;
 dataCount:number; reasons:string[]; details:Indicator[]; cross?:'golden'|'death'|null;
 sourceName:string; sourceUrl:string; dataSourceUrl?:string; licenseNote:string; adjustment?:string;
}
export interface Dashboard {
 version:1; rulesVersion:string; generatedAt:string; expectedTaiwanSession:string; scheduleText?:string; markets:MarketView[];
 sentiment:{id:string; name:string; label:string; value:number|null; status:string; url:string}[];
 research:{status:string;note:string};
}
export function parseDashboard(data:unknown):Dashboard {
 const d=data as Dashboard;
 if (!d || d.version!==1 || !Array.isArray(d.markets) || !Array.isArray(d.sentiment) || !Number.isFinite(Date.parse(d.generatedAt)) || !d.research) throw Error('Invalid dashboard');
 for (const m of d.markets) {
  if (!m.id || !m.name || !Array.isArray(m.sparkline) || !Array.isArray(m.history) || !Array.isArray(m.reasons) || !Array.isArray(m.details) || !['fresh','stale','holiday','unavailable'].includes(m.status)) throw Error('Invalid market');
  for(const v of [m.close,m.changePct,m.buyScore,m.sellScore,...m.sparkline]) if(v!==null && (typeof v!=='number' || !Number.isFinite(v))) throw Error('Invalid numeric data');
  for(const v of [m.buyScore,m.sellScore]) if(v!==null && (v<1||v>10)) throw Error('Invalid score');
 }
 return d;
}
export const number=(v:number|null, digits=2)=>v===null?'—':new Intl.NumberFormat('en-US',{minimumFractionDigits:digits,maximumFractionDigits:digits}).format(v);
export const safeUrl=(url:string)=>{try {const u=new URL(url); return u.protocol==='https:'?u.href:'#';} catch{return '#';}};
