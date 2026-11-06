import { useEffect, useRef, useState } from 'react';
import { X, ArrowUpRight, Info, ShieldCheck, FlaskConical, Layers3 } from 'lucide-react';
import type { Dashboard, MarketView } from '../types/market';
import { number, safeUrl } from '../types/market';
import { advice } from '../content/zh-TW';
import { ScorePair } from './MarketCard';
import { Sparkline } from './Sparkline';

type Panel='overview'|'signals'|'source';
export function DetailDialog({marketId,data,onClose}:{marketId:string|null;data:Dashboard;onClose:()=>void}){
 const ref=useRef<HTMLDialogElement>(null);const [tab,setTab]=useState<Panel>('overview');
 const m=data.markets.find(m=>m.id===marketId);const method=marketId==='method';const research=marketId==='research';
 useEffect(()=>{
  const dialog=ref.current;
  if(!dialog || !marketId)return;
  const previous=document.activeElement as HTMLElement|null;const overflow=document.body.style.overflow;
  setTab('overview');dialog.showModal();document.body.style.overflow='hidden';
  return()=>{dialog.close();document.body.style.overflow=overflow;previous?.focus();};
 },[marketId]);
 const title=method?'這分數怎麼來的？':research?'研究筆記與資料狀態':`${m?.name??'市場'}・陪葬攻略`;
 return <dialog ref={ref} aria-labelledby="dialog-title" className="detail-dialog" onKeyDown={e=>{
  if(e.key!=='Tab')return;
  const items=Array.from(e.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], [tabindex="0"]')).filter(el=>el.getClientRects().length>0);
  if(!items.length)return;
  const index=items.indexOf(document.activeElement as HTMLElement);
  e.preventDefault();items[(index+(e.shiftKey?-1:1)+items.length)%items.length].focus();
 }} onCancel={e=>{e.preventDefault();onClose();}} onPointerDown={e=>{if(e.target===e.currentTarget)(e.currentTarget as HTMLDialogElement).dataset.outside='yes';}} onPointerUp={e=>{const d=e.currentTarget;if(e.target===d && d.dataset.outside==='yes')onClose();delete d.dataset.outside;}}>
  <div className="dialog-shell"><header className="dialog-header"><div><span className="eyebrow">THE DAILY FIELD NOTES</span><h2 id="dialog-title">{title}</h2></div><button className="icon-button" aria-label="關閉視窗" onClick={onClose}><X size={21}/></button></header>
  {m&&<div className="dialog-tabs" role="tablist" aria-label="標的詳情">{([['overview','局勢'],['signals','訊號'],['source','資料']] as const).map(([id,label])=><button key={id} role="tab" id={`tab-${id}`} aria-selected={tab===id} aria-controls={`panel-${id}`} onClick={()=>setTab(id)}>{label}</button>)}</div>}
  <div className="dialog-content">
   {method?<Method/>:research?<Research data={data}/>:m?<div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
    {tab==='overview'?<Overview market={m}/>:tab==='signals'?<Signals market={m}/>:<Source market={m}/>}
   </div>:null}
  </div><footer className="dialog-footer"><Info size={14}/><span>有據可查地看行情，把節奏留給自己。</span></footer></div>
 </dialog>
}
function Overview({market:m}:{market:MarketView}){
 return <><div className="detail-quote"><span className="eyebrow">{m.symbol} · {m.sessionDate??'待接資料'}</span><strong>{number(m.close)}</strong><span>{advice(m)}</span></div><Sparkline values={m.history.length>1?m.history.map(p=>p.close):m.sparkline} positive={(m.changePct??0)>=0} large/>
 <div className="chart-caption"><span>{m.history[0]?.date??'尚無歷史'}</span><span>{m.history.length?`${m.history.length} 筆調整口徑收盤`:'等待歷史資料'}</span><span>{m.sessionDate??'—'}</span></div><ScorePair market={m}/>
 <div className="note-block"><Info size={17}/><div><strong>今天的觀察</strong><p>{m.reasons.join('；')}</p>{m.cross&&<p>{m.cross==='golden'?'今日發生50／200日黃金交叉':'今日發生50／200日死亡交叉'}；交叉事件與持續站在線上分開記錄。</p>}</div></div>
 {m.leveraged&&<div className="note-block risk"><Layers3 size={17}/><div><strong>正二刺激席，節奏要另外看</strong><p>每日槓桿重設，多日報酬不等於原指數報酬乘二。技術觀察不直接轉換成長期陪葬建議。</p></div></div>}
 <p className="fine-print">分數為研究規則的支持程度；無持倉資料，不提供張數或自動下單。</p></>
}
function Signals({market:m}:{market:MarketView}){
 return <><div className="section-intro"><span className="eyebrow">SIGNAL BREAKDOWN</span><h3>每一分，都有來由。</h3><p>相關指標分組計算，避免同一段行情重複投票。</p></div>{m.details.length?<div className="indicator-list">{m.details.map(d=><div className="indicator" key={d.name}><div><strong>{d.name}</strong><span>{d.value}</span></div><div><span className="mint-text">陪葬 {number(d.buyScore,1)}</span><span className="lavender-text">躲噴 {number(d.sellScore,1)}</span></div></div>)}</div>:<div className="empty-note"><FlaskConical size={26}/><h3>指標還在暖機。</h3><p>{m.reasons[0]}</p><p>目前累積 {m.dataCount} 筆；完整評分至少需要400個交易日，並確認分割與配息調整。</p></div>}<p className="fine-print">ADX 與 ATR 是風險濾網，不給方向分數；「—」代表不適用或資料不足。</p></>
}
function Source({market:m}:{market:MarketView}){
 return <><div className="section-intro"><span className="eyebrow">PROVENANCE</span><h3>先知道資料從哪裡來。</h3></div><dl className="source-list"><div><dt>行情來源</dt><dd>{m.sourceName}</dd></div><div><dt>收盤交易日</dt><dd>{m.sessionDate??'尚無資料'}</dd></div><div><dt>歷史筆數</dt><dd>{m.dataCount}</dd></div><div><dt>最近成功抓取</dt><dd>{m.lastSuccessfulFetchAt?new Date(m.lastSuccessfulFetchAt).toLocaleString('zh-TW',{timeZone:'Asia/Taipei',hour12:false}):'尚未記錄'}</dd></div><div><dt>預期最新交易日</dt><dd>{m.expectedSession??'—'}</dd></div><div><dt>價格口徑</dt><dd>{m.adjustment??'待確認'}</dd></div><div><dt>授權說明</dt><dd>{m.licenseNote}</dd></div></dl><a className="external-link" href={safeUrl(m.dataSourceUrl??m.sourceUrl)} target="_blank" rel="noreferrer">前往資料來源<ArrowUpRight size={16}/></a><a className="external-link secondary-link" href={safeUrl(m.sourceUrl)} target="_blank" rel="noreferrer">查看標的官方頁<ArrowUpRight size={16}/></a></>
}
function Method(){
 const groups=[['長期趨勢','50 / 200日均線、方向與相對位置',40],['高點回落','距近252交易日高點的回落程度',25],['進場節奏','RSI、KD、布林通道平均',25],['動能確認','MACD與柱狀體變化',10]] as const;
 return <><div className="section-intro"><span className="eyebrow">RULES, NOT GUESSES</span><h3>名字鬧一點，規則清楚一點。</h3><p>陪葬＝買進／加碼支持；躲噴＝賣出／減碼支持。兩者獨立計算，分數不是獲利機率。</p></div><div className="weight-list">{groups.map(([name,description,weight])=><div key={name}><header><strong>{name}</strong><span>{weight}%</span></header><div className="weight-track"><i style={{width:`${weight*2}%`}}/></div><p>{description}</p></div>)}</div><div className="note-block"><ShieldCheck size={18}/><div><strong>還有幾道確認，不只看總分</strong><p>長期下跌趨勢限制陪葬分上限；高等級需要至少三組支持、連續三個新交易日確認。休市與同日重跑不算新的一天。</p></div></div><p className="fine-print">躲噴分：長期趨勢惡化50%＋短線反轉30%＋MACD轉弱20%。VIX／CNN只作背景；這是尚待長期回測驗證的研究規則。</p></>
}
function Research({data}:{data:Dashboard}){
 return <><div className="section-intro"><span className="eyebrow">AN HONEST RESEARCH LOG</span><h3>先做功課，再談神準。</h3><p>{data.research.note}</p></div><div className="note-block"><FlaskConical size={18}/><div><strong>驗證時，比什麼？</strong><p>同樣現金流，比較固定投入、80%核心＋20%機動、簡單均線法；計入費用、配息與閒置現金，保留樣本外時間區段。</p></div></div><div className="source-list">{data.markets.map(m=><div key={m.id}><span>{m.name}</span><span>{m.dataCount} 筆 · {m.buyScore===null?'尚無完整評分':'公式已運算'}</span></div>)}</div><p className="fine-print">首版回測不實際執行躲噴交易；正二與海外指數僅做訊號分析。未驗證的結果不宣稱能打敗固定投入。</p></>
}
