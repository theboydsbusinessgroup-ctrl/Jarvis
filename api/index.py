from __future__ import annotations

import hmac
from html import escape
import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException, Request, Response
from threading import BoundedSemaphore
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse, FileResponse

from src.core.health_aggregator import aggregate, load_registry
from src.core.orchestration_gate import OrchestrationGate
from src.core.policy_engine import PolicyEngine
from src.core.resource_allocator import ResourceAllocator
from src.core.revenue_ledger import RevenueLedger
from src.core.command_router import route_command
from src.integrations.hermes_agent import delegate_to_hermes
from src.integrations.revenue_recovery import load_recovery_snapshot
from src.integrations.second_brain import call_second_brain
from src.core.conversation import converse, proxy_conversation
from src.core.owner_session import COOKIE, SESSION_SECONDS, authenticated, issue_session, owner_key, rate_limit, require_owner, require_same_origin

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "contracts" / "portfolio-registry.json"
POLICY_PATH = ROOT / "config" / "autonomy-policy.json"
ORCHESTRATION_PATH = ROOT / "config" / "orchestration-policy.json"
ALLOCATION_PATH = ROOT / "config" / "resource-allocation.json"
DASHBOARD_PATH = ROOT / "web" / "dashboard.html"
RECOVERY_PATH = ROOT / "data" / "revenue-recovery.json"

app = FastAPI(title="JARVIS Control Plane", version="0.3.0")
CONVERSATION_SLOTS = BoundedSemaphore(2)


def build_state() -> dict[str, Any]:
    registry = load_registry(REGISTRY_PATH)
    health = aggregate(registry)
    allocator = ResourceAllocator.from_file(ALLOCATION_PATH)
    ledger = RevenueLedger()
    recovery = load_recovery_snapshot(RECOVERY_PATH)
    return {
        "service": "jarvis-control-plane",
        "mode": "read_only",
        "schema_version": "1.2",
        "portfolio": health,
        "allocation": allocator.config["baseline_percent"],
        "verified_revenue": {**ledger.summary(), "status": "not_connected", "observed_at": None,
                             "note": "No durable authoritative revenue feed is connected to this endpoint. Empty ledger totals do not establish portfolio revenue."},
        "revenue_recovery": recovery,
        "guardrails": {
            "revenue_truth": "verified_only",
            "recovery_value_is_not_revenue": True,
            "domain_systems_authoritative": True,
            "writes_enabled": False,
            "second_brain_advisory_only": True,
            "action_control_plane": "implemented_not_wired_to_live_connectors",
            "tool_policy_default": "fail_closed",
            "approval_checkpoint_backend": "local_adapter_only_shared_backend_required_for_serverless_writes",
            "orchestration_gate": "implemented_bounded_pilot",
            "protocol_boundary": "mcp_tools_data_a2a_agents_contract_only",
        },
    }


@app.get("/health")
def health() -> dict[str, Any]:
    state = build_state()
    return {"status": "ok", "service": state["service"], "mode": state["mode"], "project_count": state["portfolio"]["project_count"], "recovery_signal_status": state["revenue_recovery"]["status"]}


@app.get("/api/control-plane")
def control_plane() -> dict[str, Any]:
    return build_state()


@app.get("/api/projects")
def projects() -> dict[str, Any]:
    state = build_state()
    return {"projects": state["portfolio"]["projects"], "counts": state["portfolio"]["counts"], "action_queue": state["portfolio"]["action_queue"], "needs_user": state["portfolio"]["needs_user"]}


@app.get("/api/projects/{project_id}")
def project(project_id: str) -> dict[str, Any]:
    for item in build_state()["portfolio"]["projects"]:
        if item["id"] == project_id:
            return item
    raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/revenue")
def revenue() -> dict[str, Any]:
    return build_state()["verified_revenue"]


@app.get("/api/recovery")
def recovery() -> dict[str, Any]:
    return build_state()["revenue_recovery"]


@app.get("/api/allocation")
def allocation() -> dict[str, Any]:
    allocator = ResourceAllocator.from_file(ALLOCATION_PATH)
    return {"baseline": allocator.config["baseline_percent"], "bounds": allocator.config["bounds_percent"], "rules": allocator.config["rules"]}


@app.get("/api/policy/{project_id}/{action}")
def policy(project_id: str, action: str, authority_tier: str = "UNKNOWN") -> dict[str, Any]:
    engine = PolicyEngine.from_file(POLICY_PATH)
    return engine.decide(action, project_id=project_id, context={"authority_tier": authority_tier})


class VoiceCommandRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=4000)


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ConversationRequest(VoiceCommandRequest):
    history: list[ConversationTurn] = Field(default_factory=list, max_length=12)


class LoginRequest(BaseModel):
    key: str = Field(min_length=1, max_length=256)


@app.get("/api/voice/config")
def voice_config(request: Request):
    enabled = os.getenv("HERMES_ENABLED", "").lower() in {"true", "1", "yes", "on"}
    return {"version": "voice-1", "authenticated": authenticated(request),
            "owner_login_configured": bool(owner_key()),
            "hermes_configured": bool(os.getenv("JARVIS_CONVERSATION_PROXY_URL")) or (enabled and bool(os.getenv("HERMES_API_URL")) and bool(os.getenv("HERMES_API_KEY"))),
            "device_actions_connected": False}


@app.post("/api/owner/login")
def owner_login(body: LoginRequest, request: Request, response: Response):
    require_same_origin(request)
    rate_limit("login", limit=10)
    key = owner_key()
    if not key:
        raise HTTPException(503, "Owner sign-in is not configured")
    if not hmac.compare_digest(body.key.encode(), key.encode()):
        raise HTTPException(401, "Incorrect owner access code")
    response.set_cookie(COOKIE, issue_session(), max_age=SESSION_SECONDS,
                        secure=True, httponly=True, samesite="strict", path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"authenticated": True}


@app.post("/api/owner/logout")
def owner_logout(request: Request, response: Response):
    require_same_origin(request)
    response.delete_cookie(COOKIE, path="/")
    return {"authenticated": False}


@app.post("/api/conversation")
def conversation(body: ConversationRequest, request: Request):
    require_owner(request)
    rate_limit("conversation")
    if not CONVERSATION_SLOTS.acquire(blocking=False):
        raise HTTPException(429, "Jarvis is handling another request. Please retry shortly.")
    try:
        if os.getenv("JARVIS_CONVERSATION_PROXY_URL"):
            try:
                return proxy_conversation(body.transcript, [t.model_dump() for t in body.history])
            except Exception:
                raise HTTPException(502, "The Hermes conversation channel is unavailable. Please retry shortly.") from None
        return converse(body.transcript, build_state(), [t.model_dump() for t in body.history],
                        OrchestrationGate.from_file(ORCHESTRATION_PATH))
    finally:
        CONVERSATION_SLOTS.release()


@app.post("/api/command")
def command(request: VoiceCommandRequest) -> dict[str, Any]:
    state = build_state()
    return route_command(request.transcript, state).to_dict()


class SecondBrainRequest(BaseModel):
    task: str = Field(min_length=3, max_length=12000)
    decision_criteria: str = Field(default="", max_length=4000)
    evidence: str = Field(default="", max_length=16000)
    review_mode: Literal["parallel", "adversarial"] = "parallel"


@app.post("/api/second-brain")
def second_brain(request: SecondBrainRequest, http_request: Request) -> dict[str, Any]:
    require_owner(http_request)
    rate_limit("second-brain", limit=5)
    result = call_second_brain(task=request.task, decision_criteria=request.decision_criteria, evidence=request.evidence, review_mode=request.review_mode)
    if result.status == "not_configured":
        raise HTTPException(status_code=503, detail=result.error)
    if result.status == "error":
        raise HTTPException(status_code=502, detail=result.error)
    return result.to_dict()


def _require_hermes_probe_auth(authorization: str | None) -> None:
    key = os.getenv("HERMES_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="HERMES_API_KEY is not configured")
    expected = f"Bearer {key}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/api/hermes/probe")
def hermes_probe(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Authenticated fixed-purpose probe for the JARVIS -> Hermes production path."""
    _require_hermes_probe_auth(authorization)
    gate = OrchestrationGate.from_file(ORCHESTRATION_PATH)
    task = "Reply with exactly: JARVIS_HERMES_E2E_OK"
    context = {
        "task_id": "jarvis-hermes-e2e-probe",
        "trace_id": "jarvis-hermes-e2e-probe",
        "project_id": "jarvis",
        "objective": task,
        "constraints": ["dry-run only", "no external writes", "return only the requested probe string"],
        "authority_context": {"tier": "GREEN", "mode": "dry_run"},
        "evidence_refs": ["runtime:jarvis-hermes-production-probe"],
    }
    result = delegate_to_hermes(gate=gate, task=task, context=context, role="specialist")
    if result.status in {"disabled", "not_configured"}:
        raise HTTPException(status_code=503, detail=result.error)
    if result.status == "blocked":
        raise HTTPException(status_code=403, detail=result.error)
    if result.status == "error":
        raise HTTPException(status_code=502, detail=result.error)
    return result.to_dict()


@app.get("/api/etsy/callback", response_class=HTMLResponse)
def etsy_callback(code: str | None = None, state: str | None = None, error: str | None = None) -> str:
    if error:
        return f"<h1>Etsy authorization failed</h1><p>{escape(error)}</p>"
    if not code:
        return "<h1>Etsy OAuth callback is ready</h1><p>This endpoint is configured for Etsy authorization.</p>"
    return "<h1>Etsy authorization received</h1><p>The authorization callback reached JARVIS successfully. Return to ChatGPT to finish the connection.</p>"


@app.get("/privacy-policy"…3849 tokens truncated…Synchronizing portfolio telemetry…</div><div class="prompt" id="audio-note">Starting Jarvis…</div></div>
<form id="command-form" style="position:absolute;bottom:0;left:5%;width:90%;display:flex;gap:8px"><input id="command-text" aria-label="Message Jarvis" placeholder="Speak or type naturally…" maxlength="4000" style="flex:1;min-width:0;background:#111;color:#eee;border:1px solid #765029;border-radius:8px;padding:10px"><button class="hudbtn" type="submit">SEND</button></form></section>
<section class="data-drawer"><div class="drawer-head"><div><div class="section-title">Portfolio Signal Rail</div><div class="muted">Swipe horizontally · live system state</div></div><div class="muted" id="sync-time"></div></div><div class="rail" id="project-list"></div><div class="section-title" style="margin-top:9px">Priority Queue</div><div class="queue" id="actions"></div></section>
</div>
<div id="boot"><div class="bootbox"><div class="boot-orb"></div><div class="boot-title">JARVIS</div><div class="boot-progress-wrap"><div class="boot-progress" id="boot-progress"></div></div><div class="boot-status" id="boot-status">CORE OFFLINE</div><div class="boot-actions"><button class="bootbtn" id="init-button">INITIALIZE WITH AUDIO</button><button class="bootbtn secondary" id="silent-button">SILENT START</button></div></div></div>
<script>
const $=id=>document.getElementById(id), nice=s=>String(s||'').replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
let voiceEnabled=localStorage.getItem('jarvisVoice')!=='off',soundEnabled=localStorage.getItem('jarvisSound')!=='off',ctx=null,state='thinking',speakingTimer=null;
const lines=["Systems online. Portfolio telemetry synchronized. You may now proceed with whatever unnecessarily ambitious idea you have next.","Good to see you, Eric. The portfolio is still standing. I checked twice, for everyone’s peace of mind.","JARVIS online. Revenue systems awake, access broker armed, sarcasm operating within approved tolerances."];
function setState(s){state=s;$('core').dataset.state=s;$('state-label').textContent=s.toUpperCase()}
function updateToggles(){$('voice-toggle').classList.toggle('active',voiceEnabled);$('sound-toggle').classList.toggle('active',soundEnabled);$('voice-toggle').textContent=voiceEnabled?'VOICE':'VOICE OFF';$('sound-toggle').textContent=soundEnabled?'SFX':'SFX OFF'}
async function unlockAudio(){try{ctx=ctx||new (window.AudioContext||window.webkitAudioContext)();if(ctx.state==='suspended')await Promise.race([ctx.resume(),new Promise(r=>setTimeout(r,500))]);return ctx.state==='running'}catch(e){return false}}
function tone(freq=440,d=.09,vol=.045,type='sine'){if(!soundEnabled||!ctx||ctx.state!=='running')return;const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.setValueAtTime(freq,ctx.currentTime);g.gain.setValueAtTime(vol,ctx.currentTime);g.gain.exponentialRampToValueAtTime(.001,ctx.currentTime+d);o.connect(g);g.connect(ctx.destination);o.start();o.stop(ctx.currentTime+d)}
function bootChord(){[[164,.12],[246,.13],[329,.15],[493,.18]].forEach(([f,d],i)=>setTimeout(()=>tone(f,d,.055,i%2?'triangle':'sine'),i*110))}
function chooseVoice(){const vs=speechSynthesis.getVoices();return vs.find(v=>/Daniel|Arthur|Oliver|Alex|James|Siri/i.test(v.name)&&/^en/i.test(v.lang))||vs.find(v=>/^en-GB/i.test(v.lang))||vs.find(v=>/^en/i.test(v.lang))||vs[0]}
function speakImmediate(text){return window.jarvisSpeak?window.jarvisSpeak(text):false}
async function audioHandshake(){const ok=await unlockAudio();if(ok){tone(523,.08,.07,'triangle');setTimeout(()=>tone(784,.12,.06,'sine'),95)}if('speechSynthesis'in window){speechSynthesis.getVoices();/* Voice greeting follows boot, once. */}return ok}
function sleep(ms){return new Promise(r=>setTimeout(r,ms))}
async function startup(audio){const boot=$('boot'),p=$('boot-progress'),s=$('boot-status');boot.classList.remove('boot-hidden');if(audio){await audioHandshake();bootChord()}const stages=[[11,'POWER BUS // ONLINE'],[27,'VOICE BUS // '+(voiceEnabled?'ARMED':'MUTED')],[43,'ACCESS BROKER // VERIFIED'],[61,'PORTFOLIO NEURAL MAP // SYNCING'],[78,'REVENUE SIGNALS // CHECKING'],[91,'PERSONALITY PROTOCOL // LOADED'],[100,'JARVIS // ONLINE']];for(const [pct,msg] of stages){p.style.width=pct+'%';s.textContent=msg;if(audio)tone(220+pct*3.6,.045,.022,'triangle');await sleep(260)}const line=lines[Math.floor(Math.random()*lines.length)];$('jarvis-line').textContent=line;setState('thinking');await sleep(420);boot.classList.add('boot-hidden');if(audio){setTimeout(()=>speakImmediate(line),120)}else setState('idle')}
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;let recognition=null,listening=false;
function micLabel(on){$('mic-toggle').textContent=on?'LISTENING':'MIC';$('mic-toggle').classList.toggle('active',on)}
$('init-button').onclick=()=>window.jarvisEnableVoice?.();$('silent-button').onclick=()=>window.jarvisSleep?.();$('replay').onclick=()=>window.jarvisReboot?.();$('voice-test').onclick=async()=>{voiceEnabled=true;localStorage.setItem('jarvisVoice','on');updateToggles();const ok=await unlockAudio();if(ok){tone(660,.12,.09,'triangle');setTimeout(()=>tone(880,.14,.075),140)}speakImmediate('Voice channel confirmed. I can hear myself perfectly. A burden you will now share.');$('audio-note').textContent='If you heard that, the voice channel is working.'};$('voice-toggle').onclick=async()=>{voiceEnabled=!voiceEnabled;localStorage.setItem('jarvisVoice',voiceEnabled?'on':'off');updateToggles();if(voiceEnabled){await unlockAudio();speakImmediate('Voice protocol online.')}else if('speechSynthesis'in window)speechSynthesis.cancel()};$('sound-toggle').onclick=async()=>{soundEnabled=!soundEnabled;localStorage.setItem('jarvisSound',soundEnabled?'on':'off');updateToggles();if(soundEnabled){await unlockAudio();bootChord()}};updateToggles();if('speechSynthesis'in window)speechSynthesis.onvoiceschanged=()=>chooseVoice();
const bars=$('voice-bars');for(let i=0;i<72;i++){const b=document.createElement('span');b.className='voice-bar';b.style.transform=`rotate(${i*5}deg) translateY(-49%)`;b.style.height=(9+(i%7)*.8)+'%';bars.appendChild(b)}setInterval(()=>{if(state!=='speaking')return;[...bars.children].forEach((b,i)=>b.style.height=(7+Math.random()*15+(i%3))+'%')},90);
const canvas=$('field'),c=canvas.getContext('2d');let W,H,pts=[];function resize(){const d=devicePixelRatio||1,Wcss=canvas.clientWidth,Hcss=canvas.clientHeight;canvas.width=Wcss*d;canvas.height=Hcss*d;c.setTransform(d,0,0,d,0,0);W=Wcss;H=Hcss;pts=Array.from({length:170},(_,i)=>({a:Math.random()*Math.PI*2,r:(.17+Math.random()*.33)*Math.min(W,H),v:(Math.random()*.0025+.0008)*(i%2?1:-1),s:Math.random()*1.8+.3,o:Math.random()*.75+.12}))}function draw(t){c.clearRect(0,0,W,H);const cx=W/2,cy=H/2;for(const p of pts){p.a+=p.v*(state==='thinking'?2.4:state==='speaking'?4.1:1);const wob=Math.sin(t*.001+p.a*3)*7*(state==='thinking'?1.7:1);const x=cx+Math.cos(p.a)*(p.r+wob),y=cy+Math.sin(p.a)*(p.r+wob);c.beginPath();c.arc(x,y,p.s*(state==='speaking'?1.5:1),0,Math.PI*2);c.fillStyle=`rgba(255,${145+Math.floor(p.o*90)},${45+Math.floor(p.o*70)},${p.o})`;c.shadowBlur=state==='speaking'?12:6;c.shadowColor='rgba(255,150,45,.8)';c.fill()}requestAnimationFrame(draw)}addEventListener('resize',resize);resize();requestAnimationFrame(draw);
async function sync(){try{const r=await fetch('/api/control-plane',{cache:'no-store'});if(!r.ok)throw new Error('API '+r.status);const d=await r.json(),p=d.portfolio,rr=d.revenue_recovery||{},rm=rr.metrics||{};$('status').textContent='ONLINE';$('projects').textContent=p.project_count;$('live').textContent=(p.counts.deployment||{}).production_live||0;$('revenue').textContent=d.verified_revenue.status==='not_connected'?'UNVERIFIED':'$'+Number(d.verified_revenue.gross_revenue||0).toLocaleString();$('recovery').textContent='$'+Number(rm.recoverable_value_identified||0).toLocaleString();$('recovery-status').textContent=`${rm.ready_recovery_opportunities||0} ready · ${rm.suppressed_opportunities||0} suppressed`;$('needs').textContent=p.needs_user.length;$('sync-time').textContent='SYNC '+new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});$('project-list').innerHTML=p.projects.map(x=>`<article class="node"><div class="node-name">${x.display_name}</div><div class="node-meta">${nice(x.lifecycle)} // ${nice(x.deployment)} // ${nice(x.revenue)}</div><div class="node-action">${x.next_action||'No queued action.'}</div></article>`).join('');$('actions').innerHTML=p.action_queue.slice(0,8).map(x=>`<div class="qitem"><div class="qname">${x.display_name}${x.needs_user?' · NEEDS ERIC':''}</div><div class="qaction">${x.next_action}</div></div>`).join('')||'<div class="qitem"><div class="qaction">No queued actions.</div></div>';setTimeout(()=>{if(state==='thinking'&&!window.jarvisBusy)setState('idle')},550)}catch(e){$('status').textContent='ERROR';$('jarvis-line').textContent='Control-plane sync failed: '+e.message;setState('idle')}}sync();setInterval(sync,60000);
</script>
<script src="/voice.js?v=1"></script>
</body></html>
