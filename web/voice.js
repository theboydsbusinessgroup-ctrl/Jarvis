/* Browser voice lifecycle. iOS permissions/autoplay remain browser controlled. */
(() => {
  let wantMic = true, busy = false, speaking = false, starting = false;
  let authenticated = false, booting = true, errorCount = 0, retryTimer, epoch = 0;
  let history = [], activeUtterance = null;
  const note = text => { $('audio-note').textContent = text; };
  const markBusy = value => { busy = value; window.jarvisBusy = value; };
  const micLabel = on => {
    $('mic-toggle').textContent = on ? 'LISTENING' : wantMic ? 'ENABLE MIC' : 'MIC OFF';
    $('mic-toggle').classList.toggle('active', on);
  };
  const micBlocked = text => {
    wantMic = false; clearTimeout(retryTimer); micLabel(false); note(text); setState('idle');
  };
  function stopRecognition() {
    clearTimeout(retryTimer);
    if (recognition && (listening || starting)) {
      try { recognition.abort(); } catch (_) { /* already ended */ }
    }
  }
  function resumeListening() {
    clearTimeout(retryTimer);
    if (!wantMic || busy || speaking || booting || document.hidden || !recognition || listening || starting) return;
    retryTimer = setTimeout(() => {
      if (!wantMic || busy || speaking || document.hidden) return;
      try { starting = true; recognition.start(); }
      catch (_) { starting = false; micBlocked('Safari needs a tap. Tap ENABLE MIC to continue.'); }
    }, 350);
  }
  window.jarvisSpeak = text => {
    if (!voiceEnabled || !('speechSynthesis' in window) || document.hidden) { resumeListening(); return false; }
    speaking = true; stopRecognition();
    // Cancel a prior utterance without allowing its stale callbacks to restart the mic.
    activeUtterance = null; speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text); activeUtterance = u;
    const v = chooseVoice(); if (v) u.voice = v;
    u.rate = .93; u.pitch = .78;
    let started = false;
    const finish = () => {
      if (activeUtterance !== u) return;
      clearTimeout(speakingTimer); activeUtterance = null; speaking = false;
      setState('idle'); resumeListening();
    };
    u.onstart = () => { started = true; setState('speaking'); };
    u.onend = finish;
    u.onerror = () => { note('Audio needs permission. Tap TEST or ENABLE MIC.'); finish(); };
    speechSynthesis.speak(u);
    // Detect blocked autoplay; never open the mic while an audible reply is still playing.
    speakingTimer = setTimeout(() => {
      if (!started && activeUtterance === u) {
        activeUtterance = null; speechSynthesis.cancel(); speaking = false;
        note('Audio could not start automatically. Tap ENABLE MIC once to activate voice.');
        setState('idle'); resumeListening();
      }
    }, 2500);
    return true;
  };
  async function config() {
    try {
      const r = await fetch('/api/voice/config', {cache:'no-store'});
      if (!r.ok) throw Error('Configuration unavailable');
      const d = await r.json(); authenticated = d.authenticated;
      $('owner-toggle').textContent = authenticated ? 'SIGNED IN' : 'SIGN IN';
      if (!d.hermes_configured) note('Basic commands ready. Natural conversation needs the Hermes connection configured.');
      else if (!authenticated) note('Sign in once to use natural conversation.');
      return d;
    } catch (_) { note('Connection unavailable. Check your internet and retry.'); return null; }
  }
  async function execute(transcript) {
    if (busy || !transcript.trim()) return;
    const requestEpoch = epoch; markBusy(true); stopRecognition(); setState('thinking');
    $('jarvis-line').textContent = '“' + transcript + '”';
    try {
      const r = await fetch(authenticated ? '/api/conversation' : '/api/command', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({transcript, ...(authenticated ? {history:history.slice(-12)} : {})}),
        signal:AbortSignal.timeout(310000),
      });
      if (!r.ok) {
        if (r.status === 401) { authenticated = false; $('owner-toggle').textContent = 'SIGN IN'; }
        throw Error(r.status === 401 ? 'Sign in to continue.' : r.status === 429 ? 'Jarvis is busy. Please try again shortly.' : 'Command channel unavailable (' + r.status + ').');
      }
      const d = await r.json(); if (requestEpoch !== epoch) return;
      const reply = !authenticated && d.decision==='not_connected' ? 'Sign in once using the SIGN IN button to enable natural conversation.' : d.reply || 'Please rephrase that.';
      $('jarvis-line').textContent = reply;
      history.push({role:'user',content:transcript.slice(0,2000)}, {role:'assistant',content:reply.slice(0,2000)});
      history = history.slice(-12);
      if (d.decision === 'execute') {
        switch (d.client_action) {
          case 'refresh': await sync(); break;
          case 'reboot': markBusy(false); await window.jarvisReboot(); return;
          case 'sleep': window.jarvisSleep(); return;
          case 'voice_off': voiceEnabled=false; localStorage.setItem('jarvisVoice','off'); updateToggles(); break;
          case 'voice_on': voiceEnabled=true; localStorage.setItem('jarvisVoice','on'); updateToggles(); break;
          case 'sound_off': soundEnabled=false; localStorage.setItem('jarvisSound','off'); updateToggles(); break;
          case 'sound_on': soundEnabled=true; localStorage.setItem('jarvisSound','on'); updateToggles(); break;
          case 'show_projects': document.querySelector('.data-drawer').scrollIntoView({behavior:'smooth'}); break;
          case 'show_actions': $('actions').scrollIntoView({behavior:'smooth',block:'center'}); break;
          case 'show_revenue': $('revenue').scrollIntoView({behavior:'smooth',block:'center'}); break;
        }
      }
      markBusy(false);
      if (!voiceEnabled || d.intent === 'voice_off' || !window.jarvisSpeak(reply)) setState('idle');
      if (!speaking) resumeListening();
    } catch (e) {
      if (requestEpoch === epoch) { $('jarvis-line').textContent = e.message; setState('idle'); }
      // Don't repeatedly submit audio during an outage, expired login or timeout.
      micBlocked('Tap ENABLE MIC to retry, or type below.');
    } finally { markBusy(false); }
  }
  function setup() {
    if (!SpeechRecognition) { $('mic-toggle').disabled=true; note('This browser has no speech recognition. Use Safari or dictate into the text box.'); return; }
    recognition = new SpeechRecognition(); recognition.lang='en-US';
    recognition.interimResults=true; recognition.continuous=false;
    let finalText='', submitted=false;
    recognition.onstart=()=>{
      starting=false; listening=true; finalText=''; submitted=false; micLabel(true);
      setState('listening'); $('jarvis-line').textContent='Listening…';
    };
    recognition.onresult=e=>{
      let interim='';
      for(let i=e.resultIndex;i<e.results.length;i++) {
        const t=e.results[i][0].transcript;
        if(e.results[i].isFinal) finalText += t + ' '; else interim += t;
      }
      $('jarvis-line').textContent=finalText||interim||'Listening…';
      if(finalText.trim()) recognition.stop();
    };
    recognition.onerror=e=>{
      starting=false;
      if(e.error==='aborted') return;
      if(e.error==='no-speech' && ++errorCount < 3) return;
      micBlocked(e.error==='not-allowed' || e.error==='service-not-allowed'
        ? 'Allow microphone and speech recognition in Safari, then tap ENABLE MIC.'
        : 'Voice paused ('+e.error+'). Tap ENABLE MIC to retry.');
    };
    recognition.onend=()=>{
      starting=false; listening=false; micLabel(false);
      if(finalText.trim()&&!submitted&&!speaking&&!busy&&wantMic&&!document.hidden) {
        submitted=true; errorCount=0; execute(finalText.trim());
      } else { if(state==='listening')setState('idle'); resumeListening(); }
    };
  }
  window.jarvisEnableVoice=async()=>{
    wantMic=true; errorCount=0; booting=false;
    // Start both inside the user gesture. No await before asking Safari for access.
    unlockAudio(); if('speechSynthesis' in window)speechSynthesis.cancel();
    activeUtterance=null; speaking=false; clearTimeout(speakingTimer);
    if (!listening && !starting && recognition) {
      try { starting=true; recognition.start(); } catch (_) { starting=false; resumeListening(); }
    }
    note('Speak naturally. Say “go to sleep” to stop listening.');
    await config();
  };
  window.jarvisSleep=()=>{
    epoch++; wantMic=false; stopRecognition(); activeUtterance=null; speaking=false;
    clearTimeout(speakingTimer); if('speechSynthesis' in window)speechSynthesis.cancel();
    $('boot').classList.add('boot-hidden'); setState('idle'); micLabel(false);
    note('Standing by. Tap MIC OFF to resume, or say “Siri, Jarvis” to reopen.');
  };
  window.jarvisReboot=async()=>{
    epoch++; stopRecognition(); booting=true; wantMic=true; errorCount=0;
    await startup(true); booting=false; resumeListening();
  };
  $('mic-toggle').onclick=()=>wantMic&&(listening||starting)?window.jarvisSleep():window.jarvisEnableVoice();
  $('owner-toggle').onclick=async()=>{
    window.jarvisSleep();
    if(authenticated) {
      if(!confirm('Sign out of Jarvis on this device?')) return;
      await fetch('/api/owner/logout',{method:'POST'}); await config(); return;
    }
    const key=prompt('Enter your Jarvis owner access code. This is separate from the Hermes API key.');
    if(!key) return;
    try {
      const r=await fetch('/api/owner/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})});
      if(!r.ok) throw Error(r.status===401?'Incorrect access code.':'Sign-in unavailable.');
      await config(); await window.jarvisEnableVoice();
    } catch(e) { note(e.message); }
  };
  $('command-form').onsubmit=e=>{
    e.preventDefault(); const text=$('command-text').value.trim();
    if(!text || busy)return; $('command-text').value=''; execute(text);
  };
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden) {
      stopRecognition(); activeUtterance=null; speaking=false;
      if('speechSynthesis' in window)speechSynthesis.cancel();
      note('Voice pauses while Jarvis is in the background.');
    } else resumeListening();
  });
  window.addEventListener('pagehide',()=>window.jarvisSleep());
  setup();
  // The dashboard initializes without a button; browser permissions can still require a tap.
  (async()=>{
    const dictated = new URLSearchParams(location.hash.slice(1)).get('command');
    if(dictated) window.history.replaceState(null,'',location.pathname+location.search);
    await config(); await startup(!dictated); booting=false;
    if(dictated) await execute(dictated.slice(0,4000)); else resumeListening();
  })();
})();
