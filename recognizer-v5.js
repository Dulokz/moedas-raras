/* Recognizer V5 — visual-first.
   Strong visual matches override OCR failure for denomination/year/design.
   OCR/catalog text remains fallback only.
*/
(function(){
  const $q=s=>document.querySelector(s);
  const fallback=window.autoIdentify;
  window.autoIdentify=async function(){
    show('scanning');
    $q('#scanFront').src=$q('#front').src=photos[0];
    $q('#scanBack').src=$q('#back').src=photos[1];
    try{
      $q('#scanStatus').textContent='Comparando o desenho com referências visuais reais…';
      const visual=await window.visualIdentify?.(photos);
      if(visual && visual.similarity>=0.72){
        window.currentVisualMatch=visual;
        $q('#value').value=visual.denomination;
        $q('#year').value=visual.year;
        $q('#commemorative').checked=visual.type==='commemorative';
        $q('#anomaly').checked=false;
        const pct=Math.round(visual.similarity*100);
        $q('#detected').textContent=`Visual v5: ${labels[visual.denomination]} • ${visual.year} • ${visual.name} • referência visual ${pct}%`;
        show('identify');
        analyze();
        return;
      }
      window.currentVisualMatch=visual||null;
      $q('#scanStatus').textContent='Sem correspondência visual forte; usando leitura auxiliar…';
      return await fallback();
    }catch(err){
      console.error('Recognizer v5 visual layer',err);
      return await fallback();
    }
  };
})();
