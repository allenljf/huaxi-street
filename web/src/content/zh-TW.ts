import type { MarketView } from '../types/market';
export const brand='陪葬! 華西街';
export const filters=[['all','全部市場'],['tw','台股'],['us','美股'],['asia','日韓'],['leveraged','正二刺激席']] as const;
export function advice(m:MarketView) {
 if(m.status==='stale' || m.status==='unavailable' || m.buyScore===null || m.sellScore===null) return '資料不足，暫不評分';
 if(m.leveraged) return '正二刺激席，先看波動再入席';
 if(m.buyScore>=7 && m.sellScore>=7) return '陪葬、躲噴各有說法，先別急';
 if(m.sellScore>=7) return '躲噴警報，檢查減碼節奏';
 if(m.buyScore>=7) return m.confirmed?'陪葬訊號集結，分批入席':'訊號待確認，先留個席位';
 if(m.sellScore>=6) return '躲噴雷達亮起，留意部位';
 if(m.buyScore>=6) return '陪葬席可留，分批慢慢來';
 if(m.buyScore<3) return '陪葬先緩緩，再看一輪';
 return '先看戲，席位不急';
}
