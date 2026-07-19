import { API_BASE } from "@/lib/api-base";

export interface DiscoverySettings {
  interval_minutes: number;
  max_items: number;
  media_page_size: number;
}

export const DISCOVERY_DEFAULTS: DiscoverySettings = {
  interval_minutes: 60,
  max_items: 100,
  media_page_size: 500,
};

export async function fetchDiscoverySettings(): Promise<DiscoverySettings> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/settings/discovery`);
    if (!res.ok) return DISCOVERY_DEFAULTS;
    return { ...DISCOVERY_DEFAULTS, ...(await res.json()) };
  } catch {
    return DISCOVERY_DEFAULTS;
  }
}
