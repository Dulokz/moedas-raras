/* Visual matcher: compares captured coin photos against real-image fingerprints.
   This runs before OCR/catalog text logic. A strong visual match can identify year/design
   even when the engraved date is unreadable to OCR.
*/
(function(){
  let visualDb=null;
  async function loadVisualDb(){if(visualDb)return visualDb;const r=await fetch('data/visual-fingerprints.json',{cache:'no-store'});if(!r.ok)throw new Error('visual db unavailable');visualDb=await r.json();return visualDb}
  function loadImage(src){return new Promise((ok,fail)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=fail;im.src=src})}
  function toGrayHash(im,deg=0,size=16){
    const s=320,base=document.createElement('canvas');base.width=base.height=s;const bx=base.getContext('2d');bx.fillStyle='#777';bx.fillRect(0,0,s,s);bx.save();bx.translate(s/2,s/2);bx.rotate(deg*Math.PI/180);const scale=Math.max(s/im.width,s/im.height);const w=im.width*scale,h=im.height*scale;bx.drawImage(im,-w/2,-h/2,w,h);bx.restore();
    const c=document.createElement('canvas');c.width=size+1;c.height=size;const x=c.getContext('2d',{willReadFrequently:true});x.drawImage(base,0,0,c.width,c.height);const d=x.getImageData(0,0,c.width,c.height).data;let bits='';for(let y=0;y<size;y++)for(let xx=0;xx<size;xx++){const i=(y*(size+1)+xx)*4,j=i+4;const a=.299*d[i]+.587*d[i+1]+.114*d[i+2],b=.299*d[j]+.587*d[j+1]+.114*d[j+2];bits+=a>b?'1':'0'}let hex='';for(let i=0;i<bits.length;i+=4)hex+=parseInt(bits.slice(i,i+4),2).toString(16);return hex}
  function bitCount(n){n=n-((n>>>1)&0x55555555);n=(n&0x33333333)+((n>>>2)&0x33333333);return (((n+(n>>>4))&0x0F0F0F0F)*0x01010101)>>>24}
  function hammingHex(a,b){let d=0;for(let i=0;i<a.length;i+=8){const x=parseInt(a.slice(i,i+8),16)^parseInt(b.slice(i,i+8),16);d+=bitCount(x>>>0)}return d}
  function bestHashDistance(candidate,hashes){let best=999;for(const h of hashes)best=Math.min(best,hammingHex(candidate,h));return best}
  async function sideScores(src,refSide){const im=await loadImage(src);let best=999;for(const deg of[0,90,180,270])best=Math.min(best,bestHashDistance(toGrayHash(im,deg),refSide.hashes));return best}
  window.visualIdentify=async function(photoPair){const db=await loadVisualDb();let best=null;for(const ref of db.references){const [p0s0,p0s1,p1s0,p1s1]=await Promise.all([sideScores(photoPair[0],ref.sides[0]),sideScores(photoPair[0],ref.sides[1]),sideScores(photoPair[1],ref.sides[0]),sideScores(photoPair[1],ref.sides[1])]);const direct=p0s0+p1s1,swapped=p0s1+p1s0,total=Math.min(direct,swapped);const maxBits=512;const similarity=Math.max(0,1-total/maxBits);if(!best||similarity>best.similarity)best={...ref,similarity,distance:total,orientation:direct<=swapped?'direct':'swapped'}}return best};
})();
