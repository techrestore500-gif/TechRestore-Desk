import { apiFetch } from './client';

export type BackupResult = {
    file_name: string;
    backup_path: string;
    created_at: string;
    file_size_bytes: number;
};

export type SystemActivity = {
    activity_type: string;
    file_name: string;
    created_at: string;
    file_size_bytes: number;
    file_path: string | null;
};

export type LoanerAgreementDefaults = {
    responsibility_text: string;
    return_policy_text: string;
    signature_note_text: string;
    updated_at: string;
};

export type NotificationTemplate = {
    id: number;
    template_key: string;
    template_name: string;
    description: string;
    template_text: string;
    placeholders: string[];
    updated_at: string;
};

export type TwilioSettings = {
    account_sid: string | null;
    phone_number: string | null;
    public_webhook_base_url: string | null;
    voicemail_greeting: string | null;
    voicemail_greeting_audio_url: string | null;
    twilio_auth_token_set: boolean;
    configured: boolean;
    created_at: string | null;
    updated_at: string | null;
};

export type TwilioSettingsUpdate = {
    account_sid?: string | null;
    auth_token?: string | null;
    clear_auth_token?: boolean;
    phone_number?: string | null;
    public_webhook_base_url?: string | null;
    voicemail_greeting?: string | null;
    voicemail_greeting_audio_url?: string | null;
};

export type VoicemailRecord = {
    id: number;
    caller_number: string | null;
    called_number: string | null;
    call_sid: string | null;
    recording_sid: string | null;
    recording_url: string | null;
    recording_duration_seconds: number | null;
    transcription_text: string | null;
    notes: string | null;
    status: string;
    customer_id: number | null;
    customer_name: string | null;
    customer_phone: string | null;
    ticket_id: number | null;
    listened_at: string | null;
    archived_at: string | null;
    created_at: string;
    updated_at: string;
};

export type TwilioSetupStatus = {
    twilio_credentials_configured: boolean;
    public_webhook_base_url_configured: boolean;
    voice_webhook_url: string;
    recording_callback_url: string;
    recording_callback_route_active: boolean;
    last_voicemail: VoicemailRecord | null;
};

export type RuntimeDiagnostics = {
    database_type: string;
    database_path: string | null;
    database_url_configured: boolean;
    sqlite_under_var_data: boolean | null;
    persistence_status: string;
    warning: string | null;
    backend_online: boolean;
    backend_version: string | null;
    backend_commit: string | null;
    frontend_commit: string | null;
    environment: string | null;
    api_base_url: string | null;
    twilio_configured: boolean | null;
};

export async function createDatabaseBackup(): Promise<BackupResult> {
    const response = await apiFetch('/api/system/backup', { method: 'POST' });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as BackupResult;
}

export async function fetchSystemActivityHistory(): Promise<SystemActivity[]> {
    const response = await apiFetch('/api/system/history');
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as SystemActivity[];
}

export async function exportDataSnapshot(): Promise<{ fileName: string; blob: Blob }> {
    const response = await apiFetch('/api/system/export');
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    const disposition = response.headers.get('Content-Disposition') ?? '';
    const match = disposition.match(/filename="([^"]+)"/i);
    const fileName = match?.[1] ?? 'tech-restore-export.json';
    return {
        fileName,
        blob: await response.blob(),
    };
}

export async function fetchLoanerAgreementDefaults(): Promise<LoanerAgreementDefaults> {
    const response = await apiFetch('/api/system/loaner-agreement-defaults');
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as LoanerAgreementDefaults;
}

export async function updateLoanerAgreementDefaults(payload: Partial<LoanerAgreementDefaults>): Promise<LoanerAgreementDefaults> {
    const response = await apiFetch('/api/system/loaner-agreement-defaults', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as LoanerAgreementDefaults;
}

export async function fetchNotificationTemplates(): Promise<NotificationTemplate[]> {
    const response = await apiFetch('/api/system/notification-templates');
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as NotificationTemplate[];
}

export async function updateNotificationTemplates(payload: Record<string, { template_text: string }>): Promise<NotificationTemplate[]> {
    const response = await apiFetch('/api/system/notification-templates', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as NotificationTemplate[];
}

export async function fetchTwilioSettings(): Promise<TwilioSettings> {
    const response = await apiFetch('/api/settings/twilio');
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as TwilioSettings;
}

export async function fetchTwilioSetupStatus(): Promise<TwilioSetupStatus> {
    const response = await apiFetch('/api/settings/twilio/setup-status');
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as TwilioSetupStatus;
}

export async function fetchRuntimeDiagnostics(): Promise<RuntimeDiagnostics> {
    const response = await apiFetch('/api/system/runtime-diagnostics');
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as RuntimeDiagnostics;
}

export async function updateTwilioSettings(payload: TwilioSettingsUpdate): Promise<TwilioSettings> {
    const response = await apiFetch('/api/settings/twilio', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as TwilioSettings;
}

export async function clearTwilioSettings(): Promise<TwilioSettings> {
    const response = await apiFetch('/api/settings/twilio', { method: 'DELETE' });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as TwilioSettings;
}

export async function fetchVoicemails(): Promise<VoicemailRecord[]> {
    const response = await apiFetch('/api/voicemails');
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as VoicemailRecord[];
}

/**
 * Fetch raw voicemail audio through the backend proxy so that the Twilio
 * Basic-Auth credentials are never sent to or stored in the browser.
 * The caller is responsible for revoking the returned blob URL via
 * URL.revokeObjectURL() when it is no longer needed.
 */
export async function fetchVoicemailAudio(voicemailId: number): Promise<{ blob: Blob; contentType: string }> {
    const response = await apiFetch(`/api/voicemails/${voicemailId}/audio`);
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Could not load audio: ${response.status}`);
    }
    const contentType = response.headers.get('Content-Type') ?? 'audio/mpeg';
    const blob = await response.blob();
    return { blob, contentType };
}

export async function updateVoicemail(voicemailId: number, payload: Partial<Pick<VoicemailRecord, 'status' | 'customer_id' | 'ticket_id'>> & { note?: string }): Promise<VoicemailRecord> {
    const response = await apiFetch(`/api/voicemails/${voicemailId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
    return (await response.json()) as VoicemailRecord;
}

export async function deleteVoicemail(voicemailId: number): Promise<void> {
    const response = await apiFetch(`/api/voicemails/${voicemailId}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
}
