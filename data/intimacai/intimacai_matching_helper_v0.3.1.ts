// intimacai_matching_helper_v0.3.ts
export type Role = { label:'Top'|'Bottom'|'Switch'|'Undefined', confidence:number, top:number, bottom:number };
export type Domain = { connection:number; sensory:number; exploration:number; structure:number };

const clamp01 = (x:number)=>Math.max(0,Math.min(1,x));

function roleComplement(a:Role,b:Role){
  return clamp01(Math.max(a.top*b.bottom, b.top*a.bottom));
}
function domainSim(a:Domain,b:Domain){
  const ds=1-Math.abs(a.connection-b.connection);
  const ss=1-Math.abs(a.sensory-b.sensory);
  const es=1-Math.abs(a.exploration-b.exploration);
  const rs=1-Math.abs(a.structure-b.structure);
  return clamp01((ds+ss+es+rs)/4);
}

export function blendScore(aR:Role,bR:Role,aD:Domain,bD:Domain,jacc:number,
                           wRole=0.30,wDom=0.50,wJac=0.20){
  return clamp01(wRole*roleComplement(aR,bR)+wDom*domainSim(aD,bD)+wJac*jacc);
}
