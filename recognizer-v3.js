/* Recognizer V3 — conservative coin recognition.
   Rules:
   1) Never infer cent denomination from an isolated digit.
   2) R$1 can be recognized by REAL text and/or bimetallic visual signal.
   3) Year is searched independently with digit-only OCR over rotated ring sectors.
   4) If confidence is weak, return UNIDENTIFIED instead of inventing a value.
*/
(function(){
  const ROT=[0,90,180,270];
  const $q=s=>document.querySelector(s);

  function loadImage(src){return new Promise((ok,fail)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=fail;im.src=src})}

  function rotated(im,deg,size=1200){
    const c=document.createElement('canvas');c.width=c.height=size;
    const x=c.getContext('2d');x.fillStyle='#111';x.fillRect(0,0,size,size);
    x.save();x.translate(size/2,size/2);x.rotate(deg*Math.PI/180);
    const s=Math.min(size/im.width,size/im.height);x.drawImage(im,-im.width*s/2,-im.height*s/2,im.width*s,im.height*s);x.restore();
    return c;
  }

  function crop(base,rx,ry,rw,rh,outW=1500){
    const c=document.createElement('canvas');
    const sx=base.width*rx,sy=base.height*ry,sw=base.width*rw,sh=base.height*rh;
    c.width=outW;c.height=Math.max(420,Math.round(outW*sh/sw));
    const x=c.getContext('2d',{willReadFrequently:true});
    x.drawImage(base,sx,sy,sw,sh,0,0,c.width,c.height);
    const id=x.getImageData(0,0,c.width,c.height),d=id.data;
    for(let i=0;i<d.length;i+=4){
      const g=.299*d[i]+.587*d[i+1]+.114*d[i+2];
      const v=Math.max(0,Math.min(255,(g-128)*2.35+128));d[i]=d[i+1]=d[i+2]=v;
    }
    x.putImageData(id,0,0);return c;
  }

  async function tess(canvas, whitelist, psm='11'){
    const w=await getWorker();
    await w.setParameters({tessedit_pageseg_mode:psm,tessedit_char_whitelist:whitelist,user_defined_dpi:'300'});
    const r=await w.recognize(canvas);return (r.data.text||'').toUpperCase().replace(/\s+/g,' ').trim();
  }

  function cleanText(t){return t.replace(/[|]/g,'I').replace(/[^A-Z0-9 -]/g,' ')}
  function yearsFrom(t){
    t=t.replace(/[OQD]/g,'0').replace(/[IL]/g,'1');
    const m=t.match(/(?:19|20)\d{2}A?/g)||[];
    return m.filter(y=>{const n=+y.slice(0,4);return n>=1994&&n<=2026});
  }

  function strongValueFrom(t){
    t=cleanText(t);
    if(/\b1\s*REAL\b|\bREAL\b/.test(t)) return '1';
    if(/\b50\s*CENT(?:AVO|AVOS)?\b/.test(t)) return '0.50';
    if(/\b25\s*CENT(?:AVO|AVOS)?\b/.test(t)) return '0.25';
    if(/\b10\s*CENT(?:AVO|AVOS)?\b/.test(t)) return '0.10';
    if(/\b5\s*CENT(?:AVO|AVOS)?\b/.test(t)) return '0.05';
    if(/\b1\s*CENT(?:AVO|AVOS)?\b/.test(t)) return '0.01';
    return '';
  }

  function rgbToHsv(r,g,b){
    r/=255;g/=255;b/=255;const mx=Math.max(r,g,b),mn=Math.min(r,g,b),d=mx-mn;let h=0;
    if(d){if(mx===r)h=((g-b)/d)%6;else if(mx===g)h=(b-r)/d+2;else h=(r-g)/d+4;h*=60;if(h<0)h+=360}
    return [h,mx?d/mx:0,mx];
  }

  // Visual cue for the bimetallic R$1: warm/golden ring surrounding a neutral center.
  function bimetalScore(src){
    return loadImage(src).then(im=>{
      const c=document.createElement('canvas');c.width=c.height=260;const x=c.getContext('2d',{willReadFrequently:true});
      x.drawImage(im,0,0,260,260);const d=x.getImageData(0,0,260,260).data;
      let best=0;
      // allow imperfect centering by testing several possible coin centers
      for(const ox of [-26,0,26])for(const oy of [-26,0,26]){
        const cx=130+ox,cy=130+oy;let ringGold=0,ringN=0,centerNeutral=0,centerN=0;
        for(let yy=20;yy<240;yy+=3)for(let xx=20;xx<240;xx+=3){
          const rr=Math.hypot(xx-cx,yy-cy)/92;if(rr>1.05)continue;
          const i=(yy*260+xx)*4,[h,s,v]=rgbToHsv(d[i],d[i+1],d[i+2]);
          if(rr>.62&&rr<1.03){ringN++;if(h>25&&h<70&&s>.16&&v>.25)ringGold++}
          else if(rr<.52){centerN++;if(s<.20&&v>.22)centerNeutral++}
        }
        if(ringN&&centerN){const score=(ringGold/ringN)*.68+(centerNeutral/centerN)*.32;best=Math.max(best,score)}
      }
      return best;
    }).catch(()=>0);
  }

  async function inspect(src,label){
    const im=await loadImage(src);let textHits=[],yearHits=[];
    for(const deg of ROT){
      $q('#scanStatus').textContent=`${label}: lendo desenho e data • ${deg}°`;
      const base=rotated(im,deg);
      // broad text pass for REAL / CENTAVOS
      const txt=await tess(crop(base,.08,.18,.84,.64,1200),'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789','11');
      textHits.push(txt);yearHits.push(...yearsFrom(txt));
      // bottom sector digit pass: rotation makes this sweep all four quadrants of the rim
      const digits=await tess(crop(base,.16,.58,.68,.30,1600),'0123456789A-','7');
      textHits.push(digits);yearHits.push(...yearsFrom(digits));
      if(yearHits.length>=2 && textHits.some(strongValueFrom)) break;
    }
    return {text:textHits.join(' '),years:yearHits};
  }

  function rankYear(all,value){
    if(!all.length)return '';
    const freq={};all.forEach(y=>freq[y]=(freq[y]||0)+1);
    const ranked=Object.entries(freq).sort((a,b)=>b[1]-a[1]).map(x=>x[0]);
    if(value&&catalog?.[value]){
      const hit=ranked.find(y=>catalog[value].includes(y));if(hit)return hit;
    }
    return ranked[0]||'';
  }

  autoIdentify=async function(){
    show('scanning');
    $q('#scanFront').src=$q('#front').src=photos[0];$q('#scanBack').src=$q('#back').src=photos[1];
    try{
      const [bm1,bm2]=await Promise.all([bimetalScore(photos[0]),bimetalScore(photos[1])]);
      const a=await inspect(photos[0],'Frente');const b=await inspect(photos[1],'Verso');
      const raw=(a.text+' '+b.text).replace(/\s+/g,' ');
      const textual=strongValueFrom(raw);
      const bimetal=Math.max(bm1,bm2);
      let value='';
      if(textual==='1' || bimetal>=.42) value='1';
      else if(textual) value=textual;
      // Never guess denomination from a bare OCR digit.
      const allYears=[...a.years,...b.years];
      let year=rankYear(allYears,value);
      if(year==='2019'&&/2019\s*A|A\s*2019/.test(raw)&&(value==='0.50'||value==='0.05'))year='2019A';
      const has1994=allYears.some(y=>y.startsWith('1994'))||/1994/.test(raw);
      const has2024=allYears.some(y=>y.startsWith('2024'))||/2024/.test(raw);
      const comm=/FAO|DIREITOS|HUMAN|OLIMP|PARALIMP|BANCO\s*CENTRAL|BEIJA/.test(raw)||(value==='1'&&has1994&&has2024);

      if(value)$q('#value').value=value;
      else $q('#value').selectedIndex=-1;
      if(year)$q('#year').value=year;else $q('#year').value='';
      $q('#commemorative').checked=comm;$q('#anomaly').checked=false;

      let msg='Automático v3: ';
      if(value&&year) msg+=`${labels[value]} • ${year} • confiança forte`;
      else if(value) msg+=`${labels[value]} • ano NÃO reconhecido • REPETIR/CONFERIR`;
      else if(year) msg+=`valor NÃO reconhecido • ${year} • REPETIR/CONFERIR`;
      else msg+='moeda NÃO identificada • REPETIR FOTO';
      if(value==='1') msg+=` • bimetal ${(bimetal*100).toFixed(0)}%`;
      $q('#detected').textContent=msg;
      show('identify');
      if(value&&year) analyze();
    }catch(err){
      console.error('Recognizer v3',err);$q('#detected').textContent='Reconhecimento inconclusivo — repetir foto. Nenhum valor foi presumido.';show('identify');
    }
  };
})();
