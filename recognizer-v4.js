/* Recognizer V4 — catalog-driven identification.
   Denomination is identified conservatively; for R$1 the bimetallic structure is a primary visual cue.
   A structured catalog is loaded from data/catalog-official.json and commemoratives are matched against it.
   For bimetallic coins the outer ring is unwrapped into a horizontal strip so curved legends/dates become OCR-friendly.
*/
(function(){
  const $q=s=>document.querySelector(s);
  const ROT=[0,90,180,270];
  let catalogDb=null;

  async function loadCatalog(){
    if(catalogDb)return catalogDb;
    const r=await fetch('data/catalog-official.json',{cache:'no-store'});
    if(!r.ok)throw new Error('catalog unavailable');
    catalogDb=await r.json();return catalogDb;
  }
  function loadImage(src){return new Promise((ok,fail)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=fail;im.src=src})}
  function canvasFromImage(im,size=1200){const c=document.createElement('canvas');c.width=c.height=size;const x=c.getContext('2d');x.fillStyle='#111';x.fillRect(0,0,size,size);const s=Math.min(size/im.width,size/im.height);x.drawImage(im,(size-im.width*s)/2,(size-im.height*s)/2,im.width*s,im.height*s);return c}
  function rotateCanvas(base,deg){const c=document.createElement('canvas');c.width=c.height=base.width;const x=c.getContext('2d');x.translate(c.width/2,c.height/2);x.rotate(deg*Math.PI/180);x.drawImage(base,-c.width/2,-c.height/2);return c}
  function enhance(c,mul=2.15){const out=document.createElement('canvas');out.width=c.width;out.height=c.height;const x=out.getContext('2d',{willReadFrequently:true});x.drawImage(c,0,0);const id=x.getImageData(0,0,out.width,out.height),d=id.data;for(let i=0;i<d.length;i+=4){const g=.299*d[i]+.587*d[i+1]+.114*d[i+2];const v=Math.max(0,Math.min(255,(g-128)*mul+128));d[i]=d[i+1]=d[i+2]=v}x.putImageData(id,0,0);return out}
  function crop(base,rx,ry,rw,rh,outW=1600){const c=document.createElement('canvas');const sx=base.width*rx,sy=base.height*ry,sw=base.width*rw,sh=base.height*rh;c.width=outW;c.height=Math.max(400,Math.round(outW*sh/sw));c.getContext('2d').drawImage(base,sx,sy,sw,sh,0,0,c.width,c.height);return enhance(c)}
  async function tess(c,wl='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-$',psm='11'){const w=await getWorker();await w.setParameters({tessedit_pageseg_mode:psm,tessedit_char_whitelist:wl,user_defined_dpi:'300',preserve_interword_spaces:'1'});const r=await w.recognize(c);return (r.data.text||'').toUpperCase().replace(/\s+/g,' ').trim()}
  function normalizeText(t){return t.toUpperCase().replace(/[OQD]/g,'0').replace(/[IL|]/g,'1').replace(/[^A-Z0-9$ -]/g,' ').replace(/\s+/g,' ').trim()}
  function yearsFrom(t){const n=normalizeText(t),out=[];for(const m of n.matchAll(/(?:19|20)\d{2}A?/g)){const y=m[0],v=+y.slice(0,4);if(v>=1994&&v<=2026)out.push(y)}return out}
  function strongValue(t){const n=normalizeText(t);if(/\bREAL\b/.test(n)||/\bR\s*\$/.test(n))return'1';if(/\b50\s*CENT(?:AVO|AVOS)?\b/.test(n))return'0.50';if(/\b25\s*CENT(?:AVO|AVOS)?\b/.test(n))return'0.25';if(/\b10\s*CENT(?:AVO|AVOS)?\b/.test(n))return'0.10';if(/\b5\s*CENT(?:AVO|AVOS)?\b/.test(n))return'0.05';if(/\b1\s*CENT(?:AVO|AVOS)?\b/.test(n))return'0.01';return''}
  function hsv(r,g,b){r/=255;g/=255;b/=255;const mx=Math.max(r,g,b),mn=Math.min(r,g,b),d=mx-mn;let h=0;if(d){if(mx===r)h=((g-b)/d)%6;else if(mx===g)h=(b-r)/d+2;else h=(r-g)/d+4;h*=60;if(h<0)h+=360}return[h,mx?d/mx:0,mx]}
  async function bimetalScore(src){const im=await loadImage(src),c=document.createElement('canvas');c.width=c.height=300;c.getContext('2d').drawImage(im,0,0,300,300);const d=c.getContext('2d',{willReadFrequently:true}).getImageData(0,0,300,300).data;let best=0;for(const ox of[-22,0,22])for(const oy of[-22,0,22]){let gold=0,rn=0,neutral=0,cn=0;const cx=150+ox,cy=150+oy;for(let y=20;y<280;y+=3)for(let x=20;x<280;x+=3){const rr=Math.hypot(x-cx,y-cy)/108;if(rr>1.05)continue;const i=(y*300+x)*4,[h,s,v]=hsv(d[i],d[i+1],d[i+2]);if(rr>.62&&rr<1.02){rn++;if(h>25&&h<72&&s>.14&&v>.22)gold++}else if(rr<.52){cn++;if(s<.22&&v>.2)neutral++}}best=Math.max(best,(gold/Math.max(1,rn))*.7+(neutral/Math.max(1,cn))*.3)}return best}

  // Polar unwrap of the outer coin ring. Curved legends become approximately horizontal text.
  function unwrapRing(base,r0=.60,r1=.99,w=2200,h=300,phase=0){const out=document.createElement('canvas');out.width=w;out.height=h;const ox=out.getContext('2d',{willReadFrequently:true}),src=base.getContext('2d',{willReadFrequently:true}).getImageData(0,0,base.width,base.height),dst=ox.createImageData(w,h),cx=base.width/2,cy=base.height/2,R=base.width*.43;for(let yy=0;yy<h;yy++){const rr=R*(r0+(r1-r0)*(yy/(h-1)));for(let xx=0;xx<w;xx++){const a=phase+2*Math.PI*(xx/(w-1));const sx=Math.max(0,Math.min(base.width-1,Math.round(cx+rr*Math.cos(a)))),sy=Math.max(0,Math.min(base.height-1,Math.round(cy+rr*Math.sin(a))));const si=(sy*base.width+sx)*4,di=(yy*w+xx)*4;dst.data[di]=src.data[si];dst.data[di+1]=src.data[si+1];dst.data[di+2]=src.data[si+2];dst.data[di+3]=255}}ox.putImageData(dst,0,0);return enhance(out,2.3)}

  async function inspect(src,label,bimetal){const im=await loadImage(src),base=canvasFromImage(im);let texts=[],years=[];for(const deg of ROT){$q('#scanStatus').textContent=`${label}: lendo centro e data • ${deg}°`;const r=rotateCanvas(base,deg),txt=await tess(crop(r,.08,.16,.84,.68,1300));texts.push(txt);years.push(...yearsFrom(txt));const digits=await tess(crop(r,.15,.56,.70,.32,1800),'0123456789A-','11');texts.push(digits);years.push(...yearsFrom(digits));if(years.length>=2)break}
    if(bimetal>.35){for(const phase of[0,Math.PI/2]){$q('#scanStatus').textContent=`${label}: lendo legenda do anel`;const ring=unwrapRing(base,.60,.99,2200,320,phase);const t1=await tess(ring,'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-$','6');texts.push(t1);years.push(...yearsFrom(t1));const flip=document.createElement('canvas');flip.width=ring.width;flip.height=ring.height;const x=flip.getContext('2d');x.translate(flip.width,flip.height);x.rotate(Math.PI);x.drawImage(ring,0,0);const t2=await tess(flip,'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-$','6');texts.push(t2);years.push(...yearsFrom(t2))}}
    return{text:normalizeText(texts.join(' ')),years}
  }
  function scoreEntry(entry,text,value,bimetal){let score=0,hits=[];if(value&&entry.denomination===value){score+=3;hits.push('valor')}if(entry.material==='bimetallic'&&bimetal>.38){score+=3;hits.push('bimetal')}const req=entry.signals?.requiredAny||[];for(const s of req){const n=normalizeText(s);if(text.includes(n)){score+=6;hits.push(s)}}for(const s of(entry.signals?.supporting||[])){const n=normalizeText(s);if(text.includes(n)){score+=1.5;hits.push(s)}}if(text.includes(entry.year)){score+=4;hits.push(entry.year)}return{entry,score,hits}}
  function pickCatalog(db,text,value,bimetal){const ranked=db.coins.map(e=>scoreEntry(e,text,value,bimetal)).sort((a,b)=>b.score-a.score);return ranked[0]?.score>=8?ranked[0]:null}
  function rankYear(ys,value){if(!ys.length)return'';const f={};ys.forEach(y=>f[y]=(f[y]||0)+1);let r=Object.entries(f).sort((a,b)=>b[1]-a[1]).map(x=>x[0]);if(value&&catalog?.[value])r.sort((a,b)=>(catalog[value].includes(b)?1:0)-(catalog[value].includes(a)?1:0));return r[0]||''}

  autoIdentify=async function(){show('scanning');$q('#scanFront').src=$q('#front').src=photos[0];$q('#scanBack').src=$q('#back').src=photos[1];try{const db=await loadCatalog();const [bm1,bm2]=await Promise.all([bimetalScore(photos[0]),bimetalScore(photos[1])]);const bimetal=Math.max(bm1,bm2);const [a,b]=await Promise.all([inspect(photos[0],'Frente',bimetal),inspect(photos[1],'Verso',bimetal)]);const raw=normalizeText(a.text+' '+b.text);let value=strongValue(raw);if(!value&&bimetal>=.40)value='1';const match=pickCatalog(db,raw,value,bimetal);let year=match?.entry?.year||rankYear([...a.years,...b.years],value);if(match)value=match.entry.denomination;
      if(value)$q('#value').value=value;else $q('#value').selectedIndex=-1;if(year)$q('#year').value=year;else $q('#year').value='';const comm=!!match&&match.entry.type==='commemorative';$q('#commemorative').checked=comm;$q('#anomaly').checked=false;
      let msg='Automático v4: ';if(match){msg+=`${labels[value]} • ${year} • ${match.entry.name} • CATÁLOGO`; }else if(value&&year){msg+=`${labels[value]} • ${year} • desenho ainda não confirmado`; }else if(value){msg+=`${labels[value]} • ano NÃO reconhecido • reter/conferir`; }else msg+='moeda NÃO identificada • repetir foto';if(value==='1')msg+=` • bimetal ${(bimetal*100).toFixed(0)}%`; $q('#detected').textContent=msg;show('identify');if(value&&year)analyze();
    }catch(err){console.error('Recognizer v4',err);$q('#detected').textContent='Reconhecimento inconclusivo — moeda retida para conferência.';show('identify')}};
})();
