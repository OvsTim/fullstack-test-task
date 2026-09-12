import { apiGet } from "@/shared/api/client";
import type { AlertItem } from "@/shared/types";

export function listAlerts(): Promise<AlertItem[]> {
  return apiGet<AlertItem[]>("/alerts");
}
