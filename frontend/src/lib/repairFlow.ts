import type { QuickRepairStatus } from "../api/tickets";

export const QUICK_REPAIR_STATUSES: QuickRepairStatus[] = [
    "New Intake",
    "Diagnosing",
    "Waiting for Part",
    "In Repair",
    "Ready for Pickup",
    "Completed",
    "Canceled",
];

export const QUICK_REPAIR_STATUS_COLORS: Record<QuickRepairStatus, { bg: string; border: string; text: string }> = {
    "New Intake": { bg: "#eaf1ff", border: "#a9c2f9", text: "#264f9f" },
    "Diagnosing": { bg: "#eef4ff", border: "#b7c9f5", text: "#36589e" },
    "Waiting for Part": { bg: "#fff0e8", border: "#f4ba9f", text: "#9b4c2d" },
    "In Repair": { bg: "#e8f6ff", border: "#9ac5f0", text: "#1f4f8e" },
    "Ready for Pickup": { bg: "#f0ecff", border: "#c2b3f3", text: "#4c3f8e" },
    Completed: { bg: "#edf4ff", border: "#afc8f4", text: "#2a4f95" },
    Canceled: { bg: "#ffecee", border: "#f5b2bc", text: "#972f43" },
};

const UI_TO_BACKEND_PRIMARY: Record<QuickRepairStatus, string> = {
    "New Intake": "New Intake",
    Diagnosing: "Needs Diagnosis",
    "Waiting for Part": "Waiting for Parts",
    "In Repair": "In Repair",
    "Ready for Pickup": "Ready for Pickup",
    Completed: "Picked Up / Closed",
    Canceled: "Not Repairable",
};

export function toBackendStatus(uiStatus: QuickRepairStatus): string {
    return UI_TO_BACKEND_PRIMARY[uiStatus];
}

export function toUiStatus(backendStatus: string): QuickRepairStatus {
    if (backendStatus === "New Intake") return "New Intake";
    if (backendStatus === "Needs Diagnosis" || backendStatus === "Diagnosed") return "Diagnosing";
    if (backendStatus === "Waiting for Parts") return "Waiting for Part";
    if (backendStatus === "Ready for Repair" || backendStatus === "In Repair") return "In Repair";
    if (backendStatus === "Ready for Pickup") return "Ready for Pickup";
    if (backendStatus === "Picked Up / Closed") return "Completed";
    if (backendStatus === "Not Repairable" || backendStatus === "Returned Unrepaired" || backendStatus === "Customer Declined") {
        return "Canceled";
    }
    return "Diagnosing";
}

export function buildTransitionPath(
    currentStatus: string,
    targetUiStatus: QuickRepairStatus,
    transitions: Record<string, string[]>
): string[] {
    const targetStatus = toBackendStatus(targetUiStatus);
    if (currentStatus === targetStatus) {
        return [];
    }

    const queue: Array<{ status: string; path: string[] }> = [{ status: currentStatus, path: [] }];
    const visited = new Set<string>([currentStatus]);

    while (queue.length > 0) {
        const node = queue.shift();
        if (!node) {
            break;
        }
        const nextStatuses = transitions[node.status] ?? [];
        for (const nextStatus of nextStatuses) {
            if (visited.has(nextStatus)) {
                continue;
            }
            const nextPath = [...node.path, nextStatus];
            if (nextStatus === targetStatus) {
                return nextPath;
            }
            visited.add(nextStatus);
            queue.push({ status: nextStatus, path: nextPath });
        }
    }

    return [];
}

export function getWorkflowAwareUiActions(
    currentStatus: string,
    transitions: Record<string, string[]>
): Array<{ status: QuickRepairStatus; pathLength: number }> {
    const currentUiStatus = toUiStatus(currentStatus);

    const ranked = QUICK_REPAIR_STATUSES
        .filter((status) => status !== currentUiStatus)
        .map((status) => {
            const path = buildTransitionPath(currentStatus, status, transitions);
            return {
                status,
                pathLength: path.length,
            };
        })
        .filter((entry) => entry.pathLength > 0)
        .sort((left, right) => {
            if (left.pathLength !== right.pathLength) {
                return left.pathLength - right.pathLength;
            }
            return QUICK_REPAIR_STATUSES.indexOf(left.status) - QUICK_REPAIR_STATUSES.indexOf(right.status);
        });

    return ranked;
}
