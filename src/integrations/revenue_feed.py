"""Authenticated, read-only revenue feed. No provider credentials or customer data."""
import json
import os
from urllib.request import Request, urlopen

FEED_URL='https://productized-ai-service.vercel.app/internal/revenue'


def load_revenue_feed():
    token=os.getenv('REVENUE_READ_TOKEN')
    if not token:return {'status':'not_connected','gross_revenue':None,'scope':'productized_ai'}
    try:
        request=Request(FEED_URL,headers={'x-revenue-token':token})
        with urlopen(request,timeout=5) as response:
            data=json.loads(response.read(65537))
        if data.get('scope')!='productized_ai' or data.get('status')!='webhook_receipts_only':
            raise ValueError('Unexpected revenue feed')
        return {key:data.get(key) for key in ('status','scope','currency','gross_revenue','live_captures',
            'observed_at','refunds','fees','contribution','settlement_verified','jobs','reconciliation')}
    except Exception:
        return {'status':'unavailable','gross_revenue':None,'scope':'productized_ai'}
