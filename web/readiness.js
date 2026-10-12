/* Live service and publishing evidence is separate from dated portfolio plans. */
(() => {
  const drawer = document.querySelector('.data-drawer');
  const section = document.createElement('section');
  section.setAttribute('aria-label', 'Live readiness checks');
  section.style.marginBottom = '18px';
  const heading = document.createElement('div');
  heading.className = 'section-title'; heading.textContent = 'Live readiness checks';
  const observed = document.createElement('p'); observed.className = 'muted';
  observed.textContent = 'Checking services and the latest YouTube publishing run…';
  const queue = document.createElement('div'); queue.className = 'queue';
  queue.setAttribute('aria-live', 'polite');
  section.append(heading, observed, queue); drawer.prepend(section);
  const probe = document.createElement('button'); probe.type = 'button';
  probe.className = 'bootbtn'; probe.textContent = 'TEST HERMES CONNECTION';
  const probeStatus = document.createElement('p'); probeStatus.className = 'muted';
  probeStatus.setAttribute('aria-live', 'polite');
  section.append(probe, probeStatus);
  probe.onclick = async () => {
    probe.disabled = true; probeStatus.textContent = 'Checking the authenticated worker…';
    try {
      const response = await fetch('/api/owner/hermes/probe', {method:'POST', signal:AbortSignal.timeout(150000)});
      if (response.status === 401) throw Error('Use SIGN IN above, then test again.');
      const result = await response.json();
      if (!response.ok || result.worker_verified !== true) throw Error(result.detail || 'Worker verification failed.');
      probeStatus.textContent = 'Hermes replied correctly at '+new Date(result.observed_at).toLocaleString()+'. No external action was performed.';
    } catch (error) { probeStatus.textContent = error.message || 'Connection unavailable. Retry shortly.'; }
    finally { probe.disabled = false; }
  };
  const names = {productized_ai_service:'Productized AI', jarvis:'Jarvis recovery feed',
    service_arbitrage:'Service Arbitrage', etsy_connector:'Etsy connection',
    autonomous_media_engine:'YouTube publishing'};
  async function refresh() {
    if (document.hidden) return;
    try {
      const response = await fetch('/api/readiness', {cache:'no-store', signal:AbortSignal.timeout(20000)});
      if (!response.ok) throw Error('Readiness unavailable');
      const report = await response.json();
      if (!Array.isArray(report.targets)) throw Error('Invalid report');
      const nodes = report.targets.map(item => {
        const row = document.createElement('article'); row.className = 'qitem';
        const title = document.createElement('div'); title.className = 'qname';
        title.textContent = `${names[item.project_id] || item.project_id} · ${String(item.status).toUpperCase()}`;
        const detail = document.createElement('div'); detail.className = 'qaction';
        detail.textContent = item.attention.length ? item.attention.join(' ') : 'Required checks passed. Revenue is verified separately.';
        row.append(title, detail); return row;
      });
      queue.replaceChildren(...nodes);
      observed.textContent = `Observed ${new Date(report.observed_at).toLocaleString()} · ${report.incident_count} incidents · ${report.attention_count} setup/freshness items`;
    } catch (_) {
      queue.replaceChildren();
      observed.textContent = 'Live verification unavailable. Portfolio plans below are dated records; retry shortly.';
    }
  }
  refresh(); setInterval(refresh, 120000);
})();
