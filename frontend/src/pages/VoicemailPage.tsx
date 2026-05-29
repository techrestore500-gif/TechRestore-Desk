import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { deleteVoicemail, fetchVoicemailAudio, fetchVoicemails, updateVoicemail, type VoicemailRecord } from "../api/system";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

export default function VoicemailPage() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});
    const [noteEditorsOpen, setNoteEditorsOpen] = useState<Record<number, boolean>>({});
    const [autoListenInFlight, setAutoListenInFlight] = useState<Record<number, boolean>>({});
    const [actionError, setActionError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);

    // Audio loading state — keyed by voicemail ID.
    // The browser <audio> element cannot attach a Bearer token to its src request,
    // so we fetch audio through apiFetch (which injects the Authorization header)
    // and hand the element a local blob URL instead.
    const [audioBlobUrls, setAudioBlobUrls] = useState<Record<number, string>>({});
    const [audioLoadErrors, setAudioLoadErrors] = useState<Record<number, string>>({});
    const [audioLoadingIds, setAudioLoadingIds] = useState<Record<number, boolean>>({});
    // Tracks IDs already queued for loading to prevent duplicate fetches.
    const queuedAudioIds = useRef<Set<number>>(new Set());

    const { data: voicemails = [], error } = useAsyncData<VoicemailRecord[]>(() => fetchVoicemails(), [refreshKey]);

    // Revoke blob URLs when they are replaced to free browser memory.
    const prevBlobUrls = useRef<Record<number, string>>({});
    useEffect(() => {
        const previous = prevBlobUrls.current;
        for (const [id, url] of Object.entries(audioBlobUrls)) {
            if (previous[Number(id)] && previous[Number(id)] !== url) {
                URL.revokeObjectURL(previous[Number(id)]);
            }
        }
        prevBlobUrls.current = audioBlobUrls;
    }, [audioBlobUrls]);

    // Revoke all remaining blob URLs when the component unmounts.
    useEffect(() => {
        return () => {
            for (const url of Object.values(prevBlobUrls.current)) {
                URL.revokeObjectURL(url);
            }
        };
    }, []);

    // Auto-load audio for every voicemail that has a recording URL.
    useEffect(() => {
        for (const voicemail of voicemails) {
            if (voicemail.recording_url && !queuedAudioIds.current.has(voicemail.id)) {
                queuedAudioIds.current.add(voicemail.id);
                void loadAudio(voicemail.id);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [voicemails]); // intentionally excludes audio state — checked synchronously via queuedAudioIds ref

    async function refresh() {
        setRefreshKey((current) => current + 1);
    }

    async function loadAudio(voicemailId: number) {
        setAudioLoadingIds((current) => ({ ...current, [voicemailId]: true }));
        setAudioLoadErrors((current) => {
            const next = { ...current };
            delete next[voicemailId];
            return next;
        });
        try {
            const { blob } = await fetchVoicemailAudio(voicemailId);
            const blobUrl = URL.createObjectURL(blob);
            setAudioBlobUrls((current) => ({ ...current, [voicemailId]: blobUrl }));
        } catch (err) {
            const message = err instanceof Error ? err.message : "Could not load audio.";
            setAudioLoadErrors((current) => ({ ...current, [voicemailId]: message }));
        } finally {
            setAudioLoadingIds((current) => ({ ...current, [voicemailId]: false }));
        }
    }

    function retryAudio(voicemailId: number) {
        // Allow the ID to be queued again so the auto-load effect or explicit retry both work.
        queuedAudioIds.current.delete(voicemailId);
        void loadAudio(voicemailId);
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
            setNoteEditorsOpen((current) => ({ ...current, [voicemailId]: false }));
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
                        const fromLabel = voicemail.caller_number ? `From: ${voicemail.caller_number}` : "From: Unknown";
                        const lineLabel = voicemail.called_number ? `Line: ${voicemail.called_number}` : "Line: Unknown";
                        const noteEditorOpen = Boolean(noteEditorsOpen[voicemail.id]);
                        return (
                            <article key={voicemail.id} style={voicemailCardStyle}>
                                <div style={cardHeaderStyle}>
                                    <div style={{ minWidth: 0 }}>
                                        <div style={fromTitleStyle}>{fromLabel}</div>
                                        {voicemail.customer_name ? <div style={customerNameStyle}>{voicemail.customer_name}</div> : null}
                                    </div>
                                    <span style={{ ...statusChip, ...statusStyles[voicemail.status as keyof typeof statusStyles] }}>{statusLabel[voicemail.status as keyof typeof statusLabel]}</span>
                                </div>

                                <div style={metaRowStyle}>
                                    <span style={metaPillStyle}>{lineLabel}</span>
                                    <span style={metaPillStyle}>Received: {receivedAt}</span>
                                    <span style={metaPillStyle}>Duration: {duration}</span>
                                    {voicemail.notes ? <span style={notePillStyle}>Note added</span> : null}
                                </div>

                                <div style={{ marginTop: "8px" }}>
                                    {voicemail.recording_url ? (
                                        audioBlobUrls[voicemail.id] ? (
                                            <audio
                                                controls
                                                style={audioPlayerStyle}
                                                src={audioBlobUrls[voicemail.id]}
                                                onPlay={() => void markListenedFromPlayback(voicemail)}
                                            />
                                        ) : audioLoadErrors[voicemail.id] ? (
                                            <div style={{ display: "grid", gap: "6px" }}>
                                                <div style={compactWarningStyle}>{audioLoadErrors[voicemail.id]}</div>
                                                <button
                                                    type="button"
                                                    style={compactActionBtnStyle}
                                                    onClick={() => retryAudio(voicemail.id)}
                                                >
                                                    Retry
                                                </button>
                                            </div>
                                        ) : (
                                            <div style={{ ...t.meta, color: "#6b7280", marginTop: 0 }}>
                                                {audioLoadingIds[voicemail.id] ? "Loading audio…" : "Audio pending…"}
                                            </div>
                                        )
                                    ) : (
                                        <div style={compactWarningStyle}>Recording audio not available yet.</div>
                                    )}
                                </div>

                                {voicemail.notes ? <pre style={noteLogStyle}>{voicemail.notes}</pre> : null}

                                <div style={{ ...t.formStack, gap: "8px", marginTop: "10px" }}>
                                    <div style={actionRowStyle}>
                                        <button
                                            type="button"
                                            style={voicemail.notes ? compactActionBtnStyle : compactPrimaryBtnStyle}
                                            onClick={() => setNoteEditorsOpen((current) => ({ ...current, [voicemail.id]: !noteEditorOpen }))}
                                        >
                                            {noteEditorOpen ? "Hide note" : voicemail.notes ? "Edit note" : "Add note"}
                                        </button>
                                        <button type="button" style={compactActionBtnStyle} onClick={() => void setStatus(voicemail.id, "listened")}>Mark listened</button>
                                        <button type="button" style={compactActionBtnStyle} onClick={() => void setStatus(voicemail.id, "archived")}>Mark done</button>
                                        <button type="button" style={compactActionBtnStyle} onClick={() => void copyCallerNumber(voicemail.caller_number)}>Copy number</button>
                                        <button type="button" style={deleteBtnStyle} onClick={() => void removeVoicemail(voicemail.id)}>Delete</button>
                                    </div>
                                    {noteEditorOpen ? (
                                        <div style={noteEditorWrapStyle}>
                                            <textarea
                                                value={noteDrafts[voicemail.id] || ""}
                                                onChange={(event) => setNoteDrafts((current) => ({ ...current, [voicemail.id]: event.target.value }))}
                                                placeholder="Add follow-up note"
                                                style={noteInputStyle}
                                            />
                                            <div style={actionRowStyle}>
                                                <button type="button" style={compactPrimaryBtnStyle} onClick={() => void saveNote(voicemail.id)}>Save note</button>
                                                <button
                                                    type="button"
                                                    style={compactActionBtnStyle}
                                                    onClick={() => setNoteEditorsOpen((current) => ({ ...current, [voicemail.id]: false }))}
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                    ) : null}
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
    padding: "14px 16px",
};

const cardHeaderStyle: React.CSSProperties = {
    display: "flex",
    justifyContent: "space-between",
    gap: "8px",
    flexWrap: "wrap",
    alignItems: "flex-start",
};

const fromTitleStyle: React.CSSProperties = {
    fontWeight: 800,
    fontSize: "0.98rem",
    letterSpacing: "0.01em",
    color: "#1d2b28",
};

const customerNameStyle: React.CSSProperties = {
    ...t.meta,
    marginTop: "2px",
    fontSize: "0.84rem",
};

const statusChip: React.CSSProperties = {
    borderRadius: "999px",
    padding: "5px 10px",
    fontWeight: 700,
    fontSize: "0.76rem",
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
    gap: "6px",
    flexWrap: "wrap",
    marginTop: "8px",
};

const metaPillStyle: React.CSSProperties = {
    borderRadius: "999px",
    padding: "4px 8px",
    border: "1px solid rgba(29,43,40,0.14)",
    background: "#ffffff",
    color: "#40514c",
    fontSize: "0.76rem",
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
    borderRadius: "10px",
    padding: "8px 10px",
    margin: "8px 0 0",
    border: "1px solid rgba(29,43,40,0.12)",
    fontSize: "0.84rem",
    lineHeight: 1.45,
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
    ...t.miniBtn,
    borderColor: "#f3b0b0",
    color: "#9b2c2c",
};

const audioPlayerStyle: React.CSSProperties = {
    width: "100%",
    height: "36px",
};

const actionRowStyle: React.CSSProperties = {
    ...t.formActionsRow,
    gap: "6px",
};

const compactActionBtnStyle: React.CSSProperties = {
    ...t.miniBtn,
    fontWeight: 600,
};

const compactPrimaryBtnStyle: React.CSSProperties = {
    ...t.miniBtn,
    background: "linear-gradient(145deg, #1f6657 0%, #184e42 100%)",
    color: "#f5efe3",
    border: "none",
    boxShadow: "0 6px 12px rgba(23, 70, 60, 0.16)",
    fontWeight: 700,
};

const noteEditorWrapStyle: React.CSSProperties = {
    display: "grid",
    gap: "6px",
};

const noteInputStyle: React.CSSProperties = {
    ...t.input,
    minHeight: "64px",
    padding: "10px 12px",
    resize: "vertical",
    fontSize: "0.94rem",
};

const compactWarningStyle: React.CSSProperties = {
    ...t.warning,
    padding: "8px 10px",
    fontSize: "0.86rem",
};
