/**
 * Technician hours logging and time-tracking API.
 *
 * Handles clock-in/clock-out sessions and manual hours entries.
 * Previously these functions were misplaced in api/tickets.ts.
 */

import { apiFetch, getJson } from "./client";

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
    const response = await apiFetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }

    return (await response.json()) as TResponse;
}

// ─── Types ────────────────────────────────────────────────────────────────────

export type HoursLog = {
    id: number;
    ticket_id: number | null;
    technician: string;
    work_date: string;
    hours_worked: number;
    work_description: string | null;
    created_at: string;
    updated_at: string;
};

export type HoursClockSession = {
    id: number;
    ticket_id: number | null;
    technician: string;
    work_description: string | null;
    clocked_in_at: string;
    clocked_out_at: string | null;
    status: string;
    elapsed_seconds: number;
    elapsed_hours: number;
    created_at: string;
    updated_at: string;
};

export type HoursClockOutResult = {
    session: HoursClockSession;
    hours_entry: HoursLog;
};

export type HoursSummary = {
    by_technician: Record<string, number>;
    total_hours: number;
    date_range: {
        start: string;
        end: string;
    };
};

// ─── API functions ────────────────────────────────────────────────────────────

/**
 * Log manual hours for a technician on a given date.
 *
 * Backend route: POST /api/hours/
 */
export async function logHours(payload: {
    technician: string;
    work_date: string;
    hours_worked: number;
    work_description?: string;
    ticket_id?: number;
}): Promise<HoursLog> {
    return postJson<HoursLog>("/api/hours/", payload);
}

/**
 * List hours entries with optional filtering.
 *
 * Backend route: GET /api/hours/
 * Trailing slash is required — the backend registers this as GET "/" under the
 * /hours prefix. Without it, FastAPI issues a 307 redirect.
 */
export async function fetchHours(
    startDate?: string,
    endDate?: string,
    technician?: string,
): Promise<HoursLog[]> {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    if (technician) params.set("technician", technician);
    const query = params.toString();
    return getJson<HoursLog[]>(`/api/hours/${query ? `?${query}` : ""}`);
}

/**
 * Fetch aggregated hours summary by technician.
 *
 * Backend route: GET /api/hours/summary
 */
export async function fetchHoursSummary(
    startDate?: string,
    endDate?: string,
    technician?: string,
): Promise<HoursSummary> {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    if (technician) params.set("technician", technician);
    const query = params.toString();
    return getJson<HoursSummary>(`/api/hours/summary${query ? `?${query}` : ""}`);
}

/**
 * Fetch the active (open) clock session for a technician, or null if none.
 *
 * Backend route: GET /api/hours/active?technician=...
 */
export async function fetchActiveClockSession(technician: string): Promise<HoursClockSession | null> {
    const params = new URLSearchParams({ technician });
    return getJson<HoursClockSession | null>(`/api/hours/active?${params.toString()}`);
}

/**
 * Clock a technician in — starts a new open session.
 *
 * Backend route: POST /api/hours/clock-in
 */
export async function clockIn(payload: {
    technician: string;
    ticket_id?: number;
    work_description?: string;
}): Promise<HoursClockSession> {
    return postJson<HoursClockSession>("/api/hours/clock-in", payload);
}

/**
 * Clock a technician out — closes the active session and writes a HoursLog.
 *
 * Backend route: POST /api/hours/clock-out
 */
export async function clockOut(payload: {
    technician: string;
    ticket_id?: number;
    work_description?: string;
}): Promise<HoursClockOutResult> {
    return postJson<HoursClockOutResult>("/api/hours/clock-out", payload);
}
