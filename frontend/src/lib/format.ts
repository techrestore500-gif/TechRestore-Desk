export function formatMoney(value: number | null | undefined, emptyLabel = "-", currency = "USD"): string {
    if (value == null || Number.isNaN(value)) {
        return emptyLabel;
    }
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
}

export function formatPhone(value: string | null | undefined, emptyLabel = "Unknown"): string {
    const raw = (value ?? "").trim();
    if (!raw) {
        return emptyLabel;
    }

    const digits = raw.replace(/\D/g, "");
    if (digits.length === 11 && digits.startsWith("1")) {
        const area = digits.slice(1, 4);
        const first = digits.slice(4, 7);
        const last = digits.slice(7);
        return `+1 ${area}-${first}-${last}`;
    }

    if (digits.length === 10) {
        const area = digits.slice(0, 3);
        const first = digits.slice(3, 6);
        const last = digits.slice(6);
        return `+1 ${area}-${first}-${last}`;
    }

    return raw;
}

export function normalizePhoneInput(value: string): string {
    const digits = value.replace(/\D/g, "").slice(0, 11);
    if (!digits) {
        return "";
    }
    if (digits.length <= 3) {
        return digits;
    }
    if (digits.length <= 6) {
        return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
    }
    if (digits.length <= 10) {
        return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }
    return `+${digits[0]} (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
}

export function formatDurationSeconds(seconds: number | null | undefined): string {
    const value = Number(seconds ?? 0);
    if (!Number.isFinite(value) || value <= 0) {
        return "0:00";
    }

    const total = Math.floor(value);
    const minutes = Math.floor(total / 60);
    const remainder = total % 60;
    return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

export function formatDeskDateTime(value: string | null | undefined, emptyLabel = "Unknown"): string {
    if (!value) {
        return emptyLabel;
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return emptyLabel;
    }

    const now = new Date();
    const sameDay =
        parsed.getFullYear() === now.getFullYear()
        && parsed.getMonth() === now.getMonth()
        && parsed.getDate() === now.getDate();

    const timeText = parsed.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    if (sameDay) {
        return `Today ${timeText}`;
    }

    return parsed.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
    });
}
