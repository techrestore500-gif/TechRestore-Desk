import { getJson } from "./client";

export type HealthResponse = {
    status: string;
    app: string;
    database_ready: boolean;
    supported_model_count: number;
    repair_category_count: number;
};

export function fetchHealth() {
    return getJson<HealthResponse>("/api/health");
}