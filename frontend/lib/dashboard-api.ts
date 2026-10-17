export type ValuationHistoryItem = {
  valuation_id: string;
  property_id: string;
  title: string;
  neighborhood: string;
  created_at: string;
  price_low: number;
  price_mid: number;
  price_high: number;
  confidence_level: number;
  model_version: string;
};

export type DashboardStats = {
  total_valuations: number;
  average_confidence: number | null;
  last_30_days: number;
  median_price_mid: number | null;
};

async function getJson<T>(path: string): Promise<T | null> {
  const apiUrl = process.env.QEYMATBAN_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(process.env.QEYMATBAN_API_KEY ? { "X-API-Key": process.env.QEYMATBAN_API_KEY } : {}),
      },
      cache: "no-store",
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchDashboardData() {
  const [history, stats] = await Promise.all([
    getJson<{ items: ValuationHistoryItem[] }>("/v1/valuations?limit=8"),
    getJson<DashboardStats>("/v1/valuations/stats"),
  ]);
  return { history: history?.items ?? null, stats };
}
