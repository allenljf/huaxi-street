import { ArrowUpRight, ArrowDownRight, ArrowRight, Clock3, Layers3 } from 'lucide-react';
import type { MarketView } from '../types/market';
import { number } from '../types/market';
import { advice } from '../content/zh-TW';
import { Sparkline } from './Sparkline';
export function ScorePair({market:m}:{market:MarketView}){
 const available=m.status!=='stale' && m.status!=='unavailable';
 return <div className="score-pair"><div><span><i className="dot mint"/>買進指數</span><strong className="mint-text">{number(available?m.buyScore:null,1)}<small> / 10</small></strong></div><div><span><i className="dot lavender"/>賣出指數</span><strong className="lavender-text">{number(available?m.sellScore:null,1)}<small> / 10</small></strong></div></div>
}
export function MarketCard({market:m,onOpen}:{market:MarketView;onOpen:(id:string)=>void}){
 const down=(m.changePct??0)<0, unavailable=m.close===null;
 const status=m.status==='stale'?'更新落後':unavailable?'來源待接':m.scoreStatus==='ready'?'已收盤':'指標暖機中';
 return <article className={`market-card glass ${unavailable?'unavailable':''}`} data-testid={`market-${m.id}`}>
  <div className="card-top"><span className={`market-icon ${m.region==='tw'?'taiwan':m.region==='us'?'american':'asian'}`}>{m.leveraged?<Layers3 size={21}/>:m.id==='2330'?'台':m.region==='tw'?'TW':m.region==='us'?'US':m.id==='nikkei'?'JP':'KR'}</span><div className="card-title"><h3>{m.name}</h3><span>{m.symbol} <b>·</b> {m.en}</span></div><span className={`status-pill ${m.status==='stale'?'warning':''}`}>{status}</span></div>
  {m.leveraged&&<div className="leveraged-note"><Layers3 size={12}/>每日槓桿重設 · 正二刺激席</div>}
  <div className="quote-row"><strong>{number(m.close)}</strong>{m.changePct!==null?<span className={down?'mint-text':'rose-text'}>{down?<ArrowDownRight size={16}/>:<ArrowUpRight size={16}/>}{m.changePct>0?'+':''}{number(m.changePct)}%</span>:<span className="muted">{unavailable?'等待可分享資料':'首筆收盤快照'}</span>}</div>
  <div className="card-chart"><Sparkline values={m.sparkline} positive={!down}/></div>
  <ScorePair market={m}/>
  <p className="advice">{advice(m)}</p><p className="reason">{m.reasons[0]}</p>
  <div className="card-bottom"><span><Clock3 size={12}/>{m.sessionDate?.replaceAll('-','.')??'尚無交易日'}</span><button onClick={e=>{e.currentTarget.focus();onOpen(m.id);}} aria-label="查看指標詳情">查看指標詳情<ArrowRight size={14}/></button></div>
 </article>
}
