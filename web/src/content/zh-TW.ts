import type { MarketView } from '../types/market';
export const brand='長期投資買進賣出參考指標';
export const filters=[['all','全部市場'],['tw','台股'],['us','美股'],['asia','日韓'],['leveraged','正二刺激席']] as const;
export function advice(m:MarketView) {
 if(m.status==='stale' || m.status==='unavailable' || m.buyScore===null || m.sellScore===null) return '資料不足，暫不評分';
 if(m.leveraged) return '正二刺激席，先看波動再入席';
 if(m.buyScore>=7 && m.sellScore>=7) return '買進、賣出訊號並存，先別急';
 if(m.sellScore>=7) return '賣出訊號偏強，檢查減碼節奏';
 if(m.buyScore>=7) return m.confirmed?'買進訊號集結，可考慮分批投入':'訊號待確認，先留個席位';
 if(m.sellScore>=6) return '賣出訊號升溫，留意部位';
 if(m.buyScore>=6) return '買進訊號升溫，可考慮分批投入';
 if(m.buyScore<3) return '買進訊號偏弱，持續觀察';
 return '先看戲，席位不急';
}
