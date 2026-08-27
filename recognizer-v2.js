/* Reconhecedor v2: leitura dirigida para moedas do Real.
   Objetivo imediato: priorizar ano/valor a partir da área da moeda,
   usando múltiplas rotações e ROIs pequenas. O motor visual definitivo
   (referência/feature matching) poderá substituir esta camada sem alterar a UI. */

(function(){
  const rotations=[0,90,180,270];

  function loadImage(src){
    return new Promise((resolve,reject)=>{
      const im=new Image();
      im.onload=()=>resolve(im);
      im.onerror=reject;
      im.src=src;
    });
  }

  function rotateCoin(im,deg){
    const c=document.createElement('canvas');
    const s=1200;
    c.width=c.height=s;
    const x=c.getContext('2d');
    x.save();
    x.translate(s/2,s/2);
    x.rotate(deg*Math.PI/180);
    const scale=Math.min(s/im.width,s/im.height);
    x.drawImage(im,-im.width*scale/2,-im.height*scale/2,im.width*scale,im.height*scale);
    x.restore();
    return c;
  }

  function roiCanvas(base,kind){
    const c=document.createElement('canvas');
    let sx=0,sy=0,sw=base.width,sh=base.height;
    if(kind==='lower'){sx=base.width*.12;sy=base.height*.48;sw=base.width*.76;sh=base.height*.42;}
    if(kind==='center'){sx=base.width*.08;sy=base.height*.22;sw=base.width*.84;sh=base.height*.58;}
    if(kind==='full'){sx=base.width*.05;sy=base.height*.05;sw=base.width*.90;sh=base.height*.90;}
    c.width=1400;c.height=Math.max(500,Math.round(1400*sh/sw));
    const x=c.getContext('2d',{willReadFrequently:true});
    x.drawImage(base,sx,sy,sw,sh,0,0,c.width,c.height);
    const id=x.getImageData(0,0,c.width,c.height),d=id.data;
    for(let i=0;i<d.length;i+=4){
      const g=.299*d[i]+.587*d[i+1]+.114*d[i+2];
      const v=Math.max(0,Math.min(255,(g-128)*2.15+128));
      d[i]=d[i+1]=d[i+2]=v;
    }
    x.putImageData(id,0,0);
    return c;
  }

  async function runOCR(canvas, whitelist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'){
    const worker=await getWorker();
    await worker.setParameters({
      tessedit_pageseg_mode:'11',
      tessedit_char_whitelist:whitelist,
      preserve_interword_spaces:'1'
    });
    const out=await worker.recognize(canvas);
    return (out.data.text||'').toUpperCase().replace(/\s+/g,' ').trim();
  }

  function yearCandidates(text){
    const t=text.replace(/[OQD]/g,'0').replace(/[IL]/g,'1');
    const hits=t.match(/(?:19|20)\d{2}A?/g)||[];
    return [...new Set(hits.filter(y=>{
      const n=Number(y.slice(0,4));
      return n>=1994&&n<=2026;
    }))];
  }

  function valueCandidates(text){
    const t=text.replace(/[^A-Z0-9]/g,' ');
    const out=[];
    if(/(?:^|\D)50(?:\D|$)/.test(t)||/50\s*CENT/.test(t))out.push('0.50');
    if(/(?:^|\D)25(?:\D|$)/.test(t)||/25\s*CENT/.test(t))out.push('0.25');
    if(/(?:^|\D)10(?:\D|$)/.test(t)||/10\s*CENT/.test(t))out.push('0.10');
    if(/(?:^|\D)5(?:\D|$)/.test(t)||/5\s*CENT/.test(t))out.push('0.05');
    if(/1\s*REAL|\bREAL\b/.test(t))out.push('1');
    if(/1\s*CENT/.test(t))out.push('0.01');
    return [...new Set(out)];
  }

  function chooseYear(allYears, value){
    if(!allYears.length)return '';
    const ranked=allYears.map(y=>({y,count:allYears.filter(x=>x===y).length}))
      .sort((a,b)=>b.count-a.count);
    if(value&&catalog?.[value]){
      const valid=ranked.find(r=>catalog[value].includes(r.y));
      if(valid)return valid.y;
    }
    return ranked[0].y;
  }

  function chooseValue(allValues,year){
    if(!allValues.length)return '';
    const ranked=allValues.map(v=>({v,count:allValues.filter(x=>x===v).length}))
      .sort((a,b)=>b.count-a.count);
    if(year){
      const valid=ranked.find(r=>catalog?.[r.v]?.includes(year));
      if(valid)return valid.v;
    }
    return ranked[0].v;
  }

  async function inspectSide(src,label){
    const im=await loadImage(src);
    const texts=[];
    const years=[];
    const values=[];
    for(const deg of rotations){
      $('#scanStatus').textContent=`${label}: procurando ano e valor • ${deg}°`;
      const base=rotateCoin(im,deg);
      for(const kind of ['lower','center']){
        const roi=roiCanvas(base,kind);
        const txt=await runOCR(roi);
        texts.push(txt);
        years.push(...yearCandidates(txt));
        values.push(...valueCandidates(txt));
      }
      if(years.length&&values.length)break;
    }
    return {texts,years,values};
  }

  autoIdentify=async function(){
    show('scanning');
    $('#scanFront').src=$('#front').src=photos[0];
    $('#scanBack').src=$('#back').src=photos[1];
    try{
      const a=await inspectSide(photos[0],'Frente');
      const b=await inspectSide(photos[1],'Verso');
      const allYears=[...a.years,...b.years];
      const allValues=[...a.values,...b.values];
      let value=chooseValue(allValues,'');
      let year=chooseYear(allYears,value);
      if(!value)value=chooseValue(allValues,year);
      if(value&&!year)year=chooseYear(allYears,value);

      const raw=[...a.texts,...b.texts].join(' ');
      if(year==='2019'&&/2019\s*A|A\s*2019/.test(raw)&&(value==='0.50'||value==='0.05'))year='2019A';
      const comm=/FAO|DIREITOS|HUMAN|OLIMP|PARALIMP|BANCO\s*CENTRAL|BEIJA/.test(raw);

      if(value)$('#value').value=value;
      if(year)$('#year').value=year;
      $('#commemorative').checked=comm;
      $('#anomaly').checked=false;

      const confidence=(value&&year)?'alta':(value||year)?'parcial':'insuficiente';
      $('#detected').textContent=`Automático v2: ${value?labels[value]:'valor NÃO reconhecido'} • ${year||'ano NÃO reconhecido'} • confiança ${confidence}`;
      show('identify');
      if(value&&year)analyze();
    }catch(err){
      console.error('Recognizer v2',err);
      $('#detected').textContent='Falha no reconhecimento automático. A moeda foi retida para conferência.';
      show('identify');
    }
  };
})();
