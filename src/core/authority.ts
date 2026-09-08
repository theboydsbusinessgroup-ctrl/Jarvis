import type { AuthorityTier } from "./event";

const defaults: Record<string, AuthorityTier> = {
  read: "GREEN",
  refresh: "GREEN",
  classify: "GREEN",
  calculate: "GREEN",
  forecast: "GREEN",
  report: "GREEN",
  bounded_retry: "GREEN",
  analytics: "GREEN",
  material_spend: "YELLOW",
  material_pricing_change: "YELLOW",
  campaign_change: "YELLOW",
  provider_change: "YELLOW",
  reputational_publish: "YELLOW",
  meaningful_capital_allocation: "YELLOW",
  large_transfer: "RED",
  credential_change: "RED",
  account_security_change: "RED",
  destructive_operation: "RED",
  legal_commitment: "RED",
  high_risk_financial_action: "RED"
};

export function authorityFor(action: string): AuthorityTier {
  return defaults[action] ?? "RED";
}

export function canAutonomouslyExecute(action: string): boolean {
  return authorityFor(action) === "GREEN";
}
