import { useState } from "react";
import { Link } from "react-router-dom";

import { deleteVoicemail, fetchVoicemails, updateVoicemail, type VoicemailRecord } from "../api/system";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

export default function VoicemailPage() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});
    const [autoListenInFlight, setAutoListenInFlight] = useState<Record<number, boolean>>({});
    const [actionError, setActionError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);

    const { data: voicemails = [], error } = useAsyncData<VoicemailRecord[]>(() => fetchVoicemails(), [refreshKey]);

    async function refresh() {
        setRefreshKey((current) => current + 1);
    }

    async function setStatus(voicemailId: number, status: "new" | "listened" | "archived") {
        try {
            setActionError(null);
            setActionMessage(null);
            await updateVoicemail(voicemailId, { status });
            await refresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not update voicemail");
        }
    }

    async function saveNote(voicemailId: number) {
        const note = noteDrafts[voicemailId]?.trim();
        if (!note) {
            return;
        }

        try {
            setActionError(null);
            setActionMessage(null);
            await updateVoicemail(voicemailId, { note });
            setNoteDrafts((current) => ({ ...current, [voicemailId]: "" }));
            await refresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not save voicemail note");
        }
    }

    async function markListenedFromPlayback(voicemail: VoicemailRecord) {
        if (voicemail.status !== "new" || autoListenInFlight[voicemail.id]) {
            return;
        }
        try {
            setAutoListenInFlight((current) => ({ ...current, [voicemail.id]: true }));
            await updateVoicemail(voicemail.id, { status: "listened" });
            await refresh();
        } catch {
            // Keep playback uninterrupted even if auto-status update fails.
        } finally {
            setAutoListenInFlight((current) => ({ ...current, [voicemail.id]: false }));
        }
    }

    async function removeVoicemail(voicemailId: number) {
        if (!window.confirm("Delete this voicemail permanently?")) {
            return;
        }
        try {
            setActionError(null);
            setActionMessage(null);
            await deleteVoicemail(voicemailId);
            setActionMessage("Voicemail deleted.");
            await refresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not delete voicemail");
        }
    }

    async function copyCallerNumber(callerNumber: string | null) {
        if (!callerNumber) {
            return;
        }
        try {
            setActionError(null);
            setActionMessage(null);
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(callerNumber);
            } else {
                const hiddenInput = document.createElement("textarea");
                hiddenInput.value = callerNumber;
                hiddenInput.setAttribute("readonly", "true");
                hiddenInput.style.position = "absolute";
                hiddenInput.style.left = "-9999px";
                document.body.appendChild(hiddenInput);
                hiddenInput.select();
                document.execCommand("copy");
                document.body.removeChild(hiddenInput);
            }
            setActionMessage("Caller number copied.");
        } catch (error) {
            setActionError(error instanceof Error ? error.message : "Could not copy caller number");
        }
    }

    return (
        <section style={{ ...t.pageWrap, gap: "18px" }}>
            <div style={{ ...t.formActionsRow, justifyContent: "space-between" }}>
                <div>
                    <h2 style={{ margin: 0 }}>Voicemail Inbox</h2>
                    <p style={{ ...t.pageIntro, marginTop: "6px" }}>Listen to voicemail messages, call customers back, and keep a simple handled status.</p>
                </div>
                <Link to="/settings" style={backLinkStyle}>Back to Settings</Link>
            </div>

            {actionError ? <div style={t.errorBanner}>{actionError}</div> : null}
            {actionMessage ? <div style={{ ...t.warning, background: "#d1fae5", color: "#065f46", borderColor: "#a7f3d0" }}>{actionMessage}</div> : null}
            {error ? <div style={t.errorBanner}>{error}</div> : null}

            {voicemails.length === 0 ? (
                <div style={t.panel}>
                    <p style={t.copy}>No voicemail messages yet. Once Twilio is configured, new recordings will appear here.</p>
                </div>
            ) : (
                <div style={{ display: "grid", gap: "14px" }}>
                    {voicemails.map((voicemail) => {
                        const receivedAt = new Date(voicemail.created_at).toLocaleString();
                        const duration = formatDuration(voicemail.recording_duration_seconds);
                        return (
                            <article key={voicemail.id} style={voicemailCardStyle}>
                                <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", flexWrap: "wrap" }}>
                                    <div>
                                        <div style={{ fontWeight: 800, fontSize: "1.05rem", letterSpacing: "0.01em" }}>{voicemail.caller_number || "Unknown caller"}</div>
                                    </div>
                                    <span style={{ ...statusChip, ...statusStyles[voicemail.status as keyof typeof statusStyles] }}>{statusLabel[voicemail.status as keyof typeof statusLabel]}</span>
                                </div>

                                <div style={metaRowStyle}>
                                    <span style={metaPillStyle}>Received: {receivedAt}</span>
                                    <span style={metaPillStyle}>Duration: {duration}</span>
                                    {voicemail.notes ? <span style={notePillStyle}>Note added</span> : null}
                                </div>

                                <div style={{ marginTop: "12px" }}>
                                    <div style={{ ...t.meta, marginTop: 0, marginBottom: "6px" }}>Playback</div>
                                    {voicemail.recording_url ? (
                                        <audio
                                            controls
                                            style={{ width: "100%" }}
                                            src={`/api/voicemails/${voicemail.id}/audio`}
                                            onPlay={() => void markListenedFromPlayback(voicemail)}
                                            onError={() => setActionError("Recording is not ready yet. Try again in a few seconds.")}
                                        />
                                    ) : (
                                        <div style={t.warning}>Recording audio not available yet.</div>
                                    )}
                                </div>

                                {voicemail.notes ? <pre style={noteLogStyle}>{voicemail.notes}</pre> : null}

                                <div style={{ ...t.formStack, gap: "10px", marginTop: "12px" }}>
                                    <textarea
                                        value={noteDrafts[voicemail.id] || ""}
                                        onChange={(event) => setNoteDrafts((current) => ({ ...current, [voicemail.id]: event.target.value }))}
                                        placeholder="Add follow-up note"
                                        style={{ ...t.input, minHeight: "88px", resize: "vertical" }}
                                    />
                                    <div style={{ ...t.formActionsRow, gap: "8px" }}>
                                        <button type="button" style={t.primaryBtn} onClick={() => void saveNote(voicemail.id)}>Add note</button>
                                        <button type="button" style={t.secondaryBtn} onClick={() => void setStatus(voicemail.id, "listened")}>Mark listened</button>
                                        <button type="button" style={t.secondaryBtn} onClick={() => void setStatus(voicemail.id, "archived")}>Mark done</button>
                                        <button type="button" style={t.secondaryBtn} onClick={() => void copyCallerNumber(voicemail.caller_number)}>Copy number</button>
                                        <button type="button" style={deleteBtnStyle} onClick={() => void removeVoicemail(voicemail.id)}>Delete</button>
                                    </div>
                                    <div style={{ ...t.meta, ...t.formActionsRow, gap: "10px" }}>
                                        <span>Called line: {voicemail.called_number || "Unknown"}</span>
                                    </div>
                                </div>
                            </article>
                        );
                    })}
                </div>
            )}
        </section>
    );
}

const voicemailCardStyle: React.CSSProperties = {
    ...t.panel,
    borderRadius: "18px",
};

const statusChip: React.CSSProperties = {
    borderRadius: "999px",
    padding: "7px 12px",
    fontWeight: 700,
    fontSize: "0.8rem",
    border: "1px solid transparent",
    alignSelf: "start",
};

const statusStyles = {
    new: { background: "#eef6ff", color: "#1e4f8d", borderColor: "#c8defa" },
    listened: { background: "#ecf8ef", color: "#1f6a3f", borderColor: "#c3eac9" },
    archived: { background: "#f3f4f6", color: "#374151", borderColor: "#d5d8df" },
} as const;

const statusLabel = {
    new: "New",
    listened: "Listened",
    archived: "Done",
} as const;

function formatDuration(seconds: number | null): string {
    const value = Number(seconds ?? 0);
    if (!Number.isFinite(value) || value <= 0) {
        return "0:00";
    }
    const total = Math.floor(value);
    const minutes = Math.floor(total / 60);
    const remainder = total % 60;
    return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

const metaRowStyle: React.CSSProperties = {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    marginTop: "10px",
};

const metaPillStyle: React.CSSProperties = {
    borderRadius: "999px",
    padding: "5px 10px",
    border: "1px solid rgba(29,43,40,0.14)",
    background: "#ffffff",
    color: "#40514c",
    fontSize: "0.82rem",
    fontWeight: 600,
};

const notePillStyle: React.CSSProperties = {
    ...metaPillStyle,
    background: "#fff5e6",
    borderColor: "#f1d4a8",
    color: "#80521f",
};

const noteLogStyle: React.CSSProperties = {
    whiteSpace: "pre-wrap",
    background: "#f8f3ea",
    borderRadius: "12px",
    padding: "12px",
    margin: "10px 0 0",
    border: "1px solid rgba(29,43,40,0.12)",
};

const backLinkStyle: React.CSSProperties = {
    textDecoration: "none",
    borderRadius: "999px",
    border: "1px solid rgba(29,43,40,0.14)",
    background: "#ffffff",
    color: "#1d2b28",
    padding: "10px 14px",
    fontWeight: 700,
};

const deleteBtnStyle: React.CSSProperties = {
    ...t.secondaryBtn,
    borderColor: "#f3b0b0",
    color: "#9b2c2c",
};
