from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_recovery_snapshot(path: str | Path, *, stale_after_hours: int = 24, now: datetime | None = None) -> dict[str, Any]:
    p=Path(path)
    if not p.exists():
        return {
            'available': False,
            'status': 'not_connected',
            'stale': True,
            'metrics': {'canonical_opportunities':0,'ready_recovery_opportunities':0,'suppressed_opportunities':0,'recoverable_value_identified':0.0,'currency':'USD','verified_recovered_revenue':0.0,'revenue_truth':'verified_only'},
            'blockers':['Revenue Recovery telemetry snapshot is not available to Jarvis.'],
            'recommended_actions':['Connect a PII-safe Revenue Recovery telemetry snapshot.'],
        }
    data=json.loads(p.read_text(encoding='utf-8'))
    generated=data.get('generated_at')
    stale=True
    age_hours=None
    if generated:
        try:
            ts=datetime.fromisoformat(generated.replace('Z','+00:00')).astimezone(timezone.utc)
            now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
            age_hours=max(0.0,(now-ts).total_seconds()/3600)
            stale=age_hours>stale_after_hours
        except ValueError:
            stale=True
    data['available']=True
    data['stale']=stale
    data['age_hours']=round(age_hours,2) if age_hours is not None else None
    data['status']='stale' if stale else 'ok'
    return data
