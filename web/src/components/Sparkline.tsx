import { useId } from 'react';
export function Sparkline({values,positive=true,large=false}:{values:number[];positive?:boolean;large?:boolean}){
 const id=useId().replace(/:/g,'');
 if(values.length<2) return <div className={`chart-empty ${large?'chart-empty-large':''}`}><span>歷史走勢累積中</span><i/><i/><i/></div>;
 const min=Math.min(...values), max=Math.max(...values),range=max-min||1;
 const points=values.map((v,i)=>`${i/(values.length-1)*600},${(1-(v-min)/range)*100+8}`).join(' ');
 const color=positive?'var(--rose)':'var(--mint)';
 return <svg className={`sparkline ${large?'large':''}`} viewBox="0 0 600 120" preserveAspectRatio="none" role="img" aria-label={`最近${values.length}筆收盤走勢，${values[values.length-1]>=values[0]?'上升':'下降'}`}>
  <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity=".15"/><stop offset="100%" stopColor={color} stopOpacity="0"/></linearGradient></defs>
  <path d={`M0,120 L${points} L600,120 Z`} fill={`url(#${id})`}/><polyline points={points} stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" fill="none" strokeLinejoin="round" strokeLinecap="round"/>
 </svg>
}
