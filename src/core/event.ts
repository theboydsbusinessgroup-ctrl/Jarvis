export type AuthorityTier = "GREEN" | "YELLOW" | "RED";

export interface JarvisEvent<TPayload extends Record<string, unknown> = Record<string, unknown>> {
  event_id: string;
  event_type: string;
  source_system: string;
  source_event_id?: string | null;
  occurred_at: string;
  received_at: string;
  idempotency_key: string;
  entity_type?: string | null;
  entity_id?: string | null;
  amount?: number | null;
  currency?: string | null;
  confidence?: number | null;
  evidence?: string[];
  payload: TPayload;
}

export function assertEventIdentity(event: JarvisEvent): void {
  if (!event.event_id || !event.idempotency_key || !event.event_type || !event.source_system) {
    throw new Error("JARVIS event identity fields are required");
  }
}

export function contributionIncome(input: {
  grossRevenue: number;
  processingFees?: number;
  marketplaceFees?: number;
  fulfillmentCost?: number;
  labor?: number;
  advertising?: number;
  infrastructure?: number;
  otherKnownExpenses?: number;
}): number {
  return input.grossRevenue
    - (input.processingFees ?? 0)
    - (input.marketplaceFees ?? 0)
    - (input.fulfillmentCost ?? 0)
    - (input.labor ?? 0)
    - (input.advertising ?? 0)
    - (input.infrastructure ?? 0)
    - (input.otherKnownExpenses ?? 0);
}
