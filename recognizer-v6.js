/* Recognizer V6 — visual-first, OCR only as fallback.
   A strong match against confirmed real-photo references sets denomination, year and design
   directly from the catalog. OCR is not allowed to override a strong visual identity.
*/
(function(){
  const $q=s=>document.querySelector(s);
  const auxiliary=window.autoIdentify;
  const VISUAL_STRONG=0.64;
  window.RECOGNITION_BUILD='6.0';

  function applyVisual(v){
    window.currentVisualMatch=v;
    $q('#value').value=v.denomination;
    $q('#year').value=v.year;
    $q('#commemorative').checked=v.type==='commemorative';
    $q('#anomaly').checked=false;
    const pct=Math.round(v.similarity*100);
    $q('#detected').textContent=`Motor V6 VISUAL: ${labels[v.denomination]} • ${v.year} • ${v.name} • ${pct}%`;
    show('identify');
    if(v.denomination&&v.year)analyze();
  }

  window.autoIdentify=async function(){
    show('scanning');
    $q('#scanFront').src=$q('#front').src=photos[0];
    $q('#scanBack').src=$q('#back').src=photos[1];
    try{
      $q('#scanStatus').textContent='Motor V6: comparando os dois lados com fotos reais do catálogo…';
      const visual=await window.visualIdentify?.(photos);
      if(visual && visual.similarity>=VISUAL_STRONG){
        applyVisual(visual);
        return;
      }
      window.currentVisualMatch=visual||null;
      $q('#scanStatus').textContent='Sem correspondência visual forte. Fazendo leitura auxiliar conservadora…';
      if(typeof auxiliary==='function'){
        await auxiliary();
        const el=$q('#detected');
        if(el)el.textContent=(el.textContent||'').replace(/^Automático v4:/,'Motor V6 auxiliar:');
        return;
      }
      $q('#detected').textContent='Motor V6: moeda ainda sem referência visual suficiente — reter/conferir.';
      show('identify');
    }catch(err){
      console.error('Recognizer V6',err);
      if(typeof auxiliary==='function'){
        await auxiliary();
        const el=$q('#detected');
        if(el)el.textContent=(el.textContent||'').replace(/^Automático v4:/,'Motor V6 auxiliar:');
      }else{
        $q('#detected').textContent='Motor V6: análise inconclusiva — reter/conferir.';
        show('identify');
      }
    }
  };
})();
