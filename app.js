const $ = s => document.querySelector(s);
let stream, step = 0, photos = [], currentCoin = null, track = null, cameras = [], focusTimer = null;
const panels = [...document.querySelectorAll('.panel')];

function show(id) {
  panels.forEach(p => p.classList.toggle('active', p.id === id));
  scrollTo(0, 0);
}

const labels = {
  '0.01': '1 centavo',
  '0.05': '5 centavos',
  '0.10': '10 centavos',
  '0.25': '25 centavos',
  '0.50': '50 centavos',
  '1': 'R$ 1,00',
  '1.00': 'R$ 1,00'
};

const API_URL = '/api/identify';

const getUserCollection = () => {
  try { return JSON.parse(localStorage.getItem('userCoinCollection') || '{}'); } catch { return {}; }
};

function saveUserCollection(col) {
  localStorage.setItem('userCoinCollection', JSON.stringify(col));
  updateSummary();
}

function updateSummary() {
  const col = getUserCollection();
  const types = Object.keys(col).length;
  const total = Object.values(col).reduce((a, x) => a + (x.qty || 0), 0);
  $('#collectionSummary').innerHTML = `🗂️ Minha Coleção: <b>${types} tipos cadastrados</b> • <b>${total} moedas guardadas</b>`;
}

function stop() {
  if (focusTimer) clearInterval(focusTimer);
  focusTimer = null;
  stream?.getTracks().forEach(t => t.stop());
  stream = null;
  track = null;
}

async function enumerateCameras() {
  const ds = await navigator.mediaDevices.enumerateDevices();
  cameras = ds.filter(d => d.kind === 'videoinput');
  const sel = $('#cameraSelect'), current = track?.getSettings?.().deviceId || '';
  sel.innerHTML = cameras.map((d, i) => `<option value="${d.deviceId}" ${d.deviceId === current ? 'selected' : ''}>${d.label || `Câmera ${i + 1}`}</option>`).join('');
  $('#cameraLabel').hidden = cameras.length < 2;
}

async function configureTrack() {
  if (!track) return;
  const caps = track.getCapabilities?.() || {}, supported = navigator.mediaDevices.getSupportedConstraints?.() || {}, adv = [];
  if (supported.focusMode && Array.isArray(caps.focusMode)) {
    if (caps.focusMode.includes('continuous')) adv.push({ focusMode: 'continuous' });
    else if (caps.focusMode.includes('single-shot')) adv.push({ focusMode: 'single-shot' });
  }
  if (adv.length) try { await track.applyConstraints({ advanced: adv }); } catch {}
  const z = $('#zoom'), zl = $('#zoomLabel');
  if (caps.zoom && Number.isFinite(caps.zoom.min) && Number.isFinite(caps.zoom.max)) {
    zl.hidden = false;
    z.min = caps.zoom.min;
    z.max = caps.zoom.max;
    z.step = caps.zoom.step || .1;
    const cur = track.getSettings().zoom ?? caps.zoom.min;
    z.value = cur;
    $('#zoomValue').textContent = `${Number(cur).toFixed(1)}×`;
  } else zl.hidden = true;
  const s = track.getSettings();
  $('#cameraInfo').textContent = `${track.label || 'Câmera'} • ${s.width || '?'}×${s.height || '?'}`;
}

async function openCamera(deviceId) {
  stop();
  const video = { width: { ideal: 3840 }, height: { ideal: 2160 }, frameRate: { ideal: 30 } };
  if (deviceId) video.deviceId = { exact: deviceId };
  else video.facingMode = { ideal: 'environment' };
  stream = await navigator.mediaDevices.getUserMedia({ video, audio: false });
  track = stream.getVideoTracks()[0];
  $('#video').srcObject = stream;
  await new Promise(r => { $('#video').onloadedmetadata = () => { $('#video').play().then(r).catch(r); }; });
  await configureTrack();
  await enumerateCameras();
  startFocusMeter();
}

async function start() {
  try {
    step = 0;
    photos = [];
    show('camera');
    $('#side').textContent = 'FRENTE';
    $('#capture').textContent = '📸 CAPTURAR FRENTE AGORA';
    await openCamera();
  } catch (e) {
    alert('Não consegui abrir a câmera. Verifique as permissões no navegador.');
  }
}

function cropCoinData() {
  const v = $('#video'), c = $('#canvas'), side = Math.min(v.videoWidth, v.videoHeight) * .58, sx = (v.videoWidth - side) / 2, sy = (v.videoHeight - side) / 2;
  c.width = 1200; c.height = 1200;
  const ctx = c.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(v, sx, sy, side, side, 0, 0, 1200, 1200);
  return c.toDataURL('image/jpeg', .85);
}

async function autoIdentify() {
  show('scanning');
  $('#scanFront').src = $('#front').src = photos[0];
  $('#scanBack').src = $('#back').src = photos[1];
  $('#scanStatus').textContent = 'Analisando características visuais com o motor de IA...';

  try {
    console.log('[CLIENT] Enviando POST /api/identify...');
    const resp = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ front: photos[0], back: photos[1] })
    });

    if (resp.ok) {
      const data = await resp.json();
      console.log('[CLIENT] Resposta da API:', data);

      if (data.identified && data.denomination) {
        const valMapped = data.denomination === '1.00' ? '1' : data.denomination;
        currentCoin = {
          id: data.coin_details?.id || `brl-${valMapped}-${data.year}`,
          v: valMapped,
          y: data.year,
          comm: data.commemorative,
          design: data.design,
          details: data.coin_details
        };

        const pct = Math.round((data.confidence || 0) * 100);
        showRichCoinDetails(data, pct);
        return;
      } else {
        // Open-Set Rejection (Moeda Desconhecida / Não Catalogada)
        showUnidentifiedResult(data);
        return;
      }
    }
  } catch (err) {
    console.warn('[CLIENT ERROR] Falha na comunicação com /api/identify:', err);
  }

  showUnidentifiedResult(null);
}

function showRichCoinDetails(data, confidencePct) {
  $('#status').className = 'status green';
  $('#status').textContent = '🟢 IDENTIFICADA AUTOMATICAMENTE COM SUCESSO';

  const valLabel = labels[data.denomination] || `R$ ${data.denomination}`;
  $('#resultTitle').textContent = `${valLabel} • Ano ${data.year}`;
  $('#resultText').textContent = `${data.design} ${data.commemorative ? '• (Emissão Comemorativa)' : ''}`;

  const details = data.coin_details || {};
  const history = details.history || {};
  const specs = details.specifications || {};
  const obverse = details.obverse || {};
  const reverse = details.reverse || {};
  const rarity = details.rarity || {};
  const errors = details.known_errors || [];
  const refs = details.references || [];

  let html = `
    <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 12px;">
      <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 6px;">🎯 Identificação IA: ${data.design}</div>
      <div>📊 <b>Confiança do Motor:</b> ${confidencePct}%</div>
      ${data.commemorative ? '<div style="color: #f1c40f; margin-top: 4px;">🏛️ <b>MOEDA COMEMORATIVA OFICIAL</b></div>' : ''}
    </div>
  `;

  if (history.short_summary || history.full_context) {
    html += `
      <div style="margin-bottom: 14px;">
        <h3>📖 História & Contexto Numismático</h3>
        <p><b>${history.title || 'História Oficial'}:</b> ${history.short_summary || ''}</p>
        <small>${history.full_context || ''}</small>
      </div>
    `;
  }

  html += `
    <div style="margin-bottom: 14px;">
      <h3>📐 Especificações Técnicas Oficiais</h3>
      <div>• <b>Material:</b> ${specs.material || 'Padrão Oficial BCB'}</div>
      <div>• <b>Diâmetro:</b> ${specs.diameter_mm ? specs.diameter_mm + ' mm' : '27 mm'} | <b>Peso:</b> ${specs.weight_g ? specs.weight_g + ' g' : '7.0 g'}</div>
      <div>• <b>Espessura:</b> ${specs.thickness_mm ? specs.thickness_mm + ' mm' : '1.95 mm'} | <b>Bordo:</b> ${specs.edge || 'Serrilhado intermitente'}</div>
      <div>• <b>Alinhamento / Eixo:</b> ${specs.alignment || 'Moeda (180°)'}</div>
      <div>• <b>Tiragem Oficial:</b> ${details.mintage ? details.mintage.toLocaleString('pt-BR') + ' peças' : 'Não informada'}</div>
      <div>• <b>Raridade Relativa:</b> ${rarity.relative_rarity || 'Comum em circulação'}</div>
    </div>
  `;

  if (obverse.description || reverse.description) {
    html += `
      <div style="margin-bottom: 14px;">
        <h3>🔍 Descrição Visual dos Lados</h3>
        <div><b>Frente (Anverso):</b> ${obverse.description || 'Padrão Oficial'}</div>
        <div><b>Verso (Reverso):</b> ${reverse.description || 'Padrão Oficial'}</div>
      </div>
    `;
  }

  if (errors.length > 0) {
    html += `
      <div style="margin-bottom: 14px;">
        <h3>🔬 Checklist de Variantes e Erros Conhecidos</h3>
        ${errors.map(e => `<div>• <b>${e}</b></div>`).join('')}
      </div>
    `;
  }

  if (refs.length > 0) {
    html += `
      <div style="margin-bottom: 10px;">
        <small><b>Fontes de Evidência Oficiais:</b> ${refs.map(r => `<a href="${r.url}" target="_blank" style="color: #3498db; text-decoration: underline;">${r.source} (Nível ${r.evidence_level})</a>`).join(' • ')}</small>
      </div>
    `;
  }

  $('#facts').innerHTML = html;
  $('#variantMatches').innerHTML = '';
  renderOwnedStatus();

  $('#saveCoin').hidden = false;
  $('#again').hidden = false;
  $('#retryScan').hidden = true;
  $('#manualFallbackBtn').hidden = true;
  $('#uncataloguedBtn').hidden = true;

  show('result');
}

function showUnidentifiedResult(apiData) {
  currentCoin = null;
  $('#status').className = 'status yellow';
  $('#status').textContent = '🟡 MOEDA NÃO IDENTIFICADA COM SEGURANÇA';
  $('#resultTitle').textContent = 'Moeda não identificada com segurança.';
  $('#resultText').textContent = 'Esta moeda pode ser uma emissão comemorativa ainda não catalogada no aplicativo, ou a captura precisa de melhor iluminação.';
  
  let reasonText = 'Nenhuma emissão conhecida no catálogo atinge a margem de aceitação mínima.';
  if (apiData && apiData.warnings && apiData.warnings.length > 0) {
    reasonText = apiData.warnings[0];
  }

  let html = `
    <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 12px;">
      <div style="font-weight: bold; margin-bottom: 4px;">🔍 Diagnóstico da IA (Open-Set OOD):</div>
      <div style="font-size: 0.9em; color: #f39c12;">${reasonText}</div>
      ${apiData && apiData.best_candidate ? `<div style="font-size: 0.85em; margin-top: 6px; color: #aaa;">Maior aproximação observada: <i>${apiData.best_candidate.design} (${Math.round((apiData.best_candidate.confidence||0)*100)}%)</i></div>` : ''}
    </div>
    <div style="margin-bottom: 10px;">
      <b>Dicas para identificação perfeita:</b><br>
      • Garanta boa iluminação ambiente (sem iluminação roxa ou sombras fortes).<br>
      • Posicione a moeda no centro da marcação da câmera.<br>
      • Se a moeda for uma emissão rara ou ainda não cadastrada, solicite a inclusão no catálogo.
    </div>
  `;

  $('#facts').innerHTML = html;
  $('#variantMatches').innerHTML = '';
  $('#ownedState').innerHTML = '';

  $('#saveCoin').hidden = true;
  $('#again').hidden = true;
  $('#retryScan').hidden = false;
  $('#uncataloguedBtn').hidden = false;
  $('#manualFallbackBtn').hidden = false;

  show('result');
}

function renderOwnedStatus() {
  if (!currentCoin) return;
  const col = getUserCollection();
  const entry = col[currentCoin.id];
  $('#ownedState').innerHTML = entry 
    ? `✅ Você possui <b>${entry.qty} exemplar(es)</b> desta moeda na sua coleção!`
    : '⭐ Esta moeda ainda não está salva na sua coleção.';
}

function saveCurrentCoinToCollection() {
  if (!currentCoin) return;
  const col = getUserCollection();
  const id = currentCoin.id;
  col[id] = col[id] || { coin_id: id, qty: 0, acquired_at: new Date().toISOString().split('T')[0] };
  col[id].qty++;
  saveUserCollection(col);
  renderOwnedStatus();
}

async function renderFullCatalogView() {
  try {
    const res = await fetch('/api/catalog');
    if (!res.ok) return;
    const data = await res.json();
    const coins = data.coins || [];

    const col = getUserCollection();
    let html = '<h3>🏛️ Catálogo Universal de Moedas do Real</h3><div class="facts">';

    coins.forEach(c => {
      const ownedEntry = col[c.id];
      html += `
        <div style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 8px;">
          <div style="font-weight: bold; font-size: 1.1em;">${ownedEntry ? '✅' : '⬜'} R$ ${c.denomination} (${c.year}) — ${c.design_name}</div>
          <small>Tiragem: ${c.mintage ? c.mintage.toLocaleString('pt-BR') : 'Sem dados'} | Material: ${c.specifications?.material || c.material || 'Padrão'}</small>
          ${ownedEntry ? `<br><small style="color: #2ecc71;">Na sua coleção: ×${ownedEntry.qty}</small>` : ''}
        </div>
      `;
    });
    html += '</div>';

    $('#collectionStats').innerHTML = `Tipos Guardados na Sua Coleção: <b>${Object.keys(col).length}</b>`;
    $('#collectionList').innerHTML = html;
  } catch (err) {
    console.warn('Erro ao carregar catálogo universal:', err);
  }
}

$('#saveCoin').onclick = saveCurrentCoinToCollection;
$('#collectionBtn').onclick = () => { renderFullCatalogView(); show('collection'); };
$('#collectionHome').onclick = () => show('home');
$('#start').onclick = start;
$('#cancel').onclick = () => { stop(); show('home'); };
$('#manual').onclick = () => show('identify');
$('#again').onclick = start;
$('#retryScan').onclick = start;
$('#uncataloguedBtn').onclick = () => alert('Solicitação registrada! Em breve esta emissão estará indexada no catálogo universal.');
$('#manualFallbackBtn').onclick = () => show('identify');
$('#edit').onclick = () => show('identify');
$('#backHome').onclick = () => show('home');

updateSummary();
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');