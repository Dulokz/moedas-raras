// Capture UX V2: automatic by default, with a large always-available manual button.
let autoStableFrames=0,autoCooldown=false,autoCountdownTimer=null,autoLastScore=0;
const AUTO_FOCUS_SCORE=900;
const AUTO_STABLE_FRAMES=3;

function resetAutoCapture(){
  autoStableFrames=0;autoLastScore=0;autoCooldown=false;
  clearInterval(autoCountdownTimer);autoCountdownTimer=null;
  const c=document.querySelector('#countdown');if(c)c.textContent='';
  document.querySelector('.camera')?.classList.remove('ready','captured');
}

function finishCapturedSide(){
  if(step++===0){
    document.querySelector('#side').textContent='VERSO';
    document.querySelector('#captureProgress').textContent='2/2';
    document.querySelector('#focusHint').textContent='Vire a moeda e centralize';
    document.querySelector('#capture').textContent='📸 CAPTURAR VERSO AGORA';
    setTimeout(()=>{autoCooldown=false;autoStableFrames=0;autoLastScore=0;document.querySelector('.camera')?.classList.remove('ready','captured')},850);
  }else{
    stop();autoIdentify();
  }
}

function captureNow(){
  if(autoCooldown||!stream)return;
  autoCooldown=true;
  photos.push(cropCoinData());
  document.querySelector('.camera')?.classList.add('captured');
  finishCapturedSide();
}

async function automaticSnap(){
  if(autoCooldown||!stream)return;
  autoCooldown=true;
  document.querySelector('.camera')?.classList.add('ready');
  let n=2;const cd=document.querySelector('#countdown');if(cd)cd.textContent=n;
  autoCountdownTimer=setInterval(()=>{
    n--;
    if(n>0){if(cd)cd.textContent=n;return}
    clearInterval(autoCountdownTimer);autoCountdownTimer=null;if(cd)cd.textContent='';
    const now=sharpness();
    if(now<AUTO_FOCUS_SCORE*.75){autoCooldown=false;autoStableFrames=0;document.querySelector('.camera')?.classList.remove('ready');return}
    photos.push(cropCoinData());document.querySelector('.camera')?.classList.add('captured');finishCapturedSide();
  },450);
}

startFocusMeter=function(){
  if(focusTimer)clearInterval(focusTimer);resetAutoCapture();
  focusTimer=setInterval(()=>{
    lastSharpness=sharpness();
    const el=document.querySelector('#focusState'),hint=document.querySelector('#focusHint');
    const delta=autoLastScore?Math.abs(lastSharpness-autoLastScore):99999;autoLastScore=lastSharpness;
    const allowedDelta=Math.max(120,lastSharpness*.18);
    if(lastSharpness>=AUTO_FOCUS_SCORE){
      el.className='focusState good';el.textContent=`🟢 NÍTIDO • ${Math.round(lastSharpness)}`;
      hint.textContent=autoCooldown?'Capturando…':'Segure por um instante';
      if(delta<=allowedDelta)autoStableFrames++;else autoStableFrames=0;
      if(autoStableFrames>=AUTO_STABLE_FRAMES&&!autoCooldown)automaticSnap();
    }else if(lastSharpness>=450){
      el.className='focusState waiting';el.textContent=`🟡 QUASE • ${Math.round(lastSharpness)}`;
      hint.textContent='Ajustando foco — ou capture manualmente';autoStableFrames=0;
    }else{
      el.className='focusState bad';el.textContent=`🔴 SEM NITIDEZ • ${Math.round(lastSharpness)}`;
      hint.textContent='Aproxime/afaste — ou capture manualmente';autoStableFrames=0;
    }
  },300);
};

const originalStart=start;
start=async function(){
  resetAutoCapture();
  document.querySelector('#captureProgress').textContent='1/2';
  document.querySelector('#captureMode').textContent='AUTO + MANUAL';
  await originalStart();
  document.querySelector('#capture').textContent='📸 CAPTURAR FRENTE AGORA';
};

document.querySelector('#capture').onclick=captureNow;
