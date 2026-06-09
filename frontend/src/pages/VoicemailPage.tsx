import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { deleteVoicemail, fetchVoicemailAudio, fetchVoicemails, updateVoicemail, type VoicemailRecord } from "../api/system";
import { useAsyncData } from "../hooks/useAsyncData";
import { formatDeskDateTime, formatDurationSeconds, formatPhone } from "../lib/format";
import { PageHeader, SectionCard } from "../components/PageChrome";
import * as t from "../styles/theme";

type VoicemailQuickFilter = "all" | "new" | "listened" | "archived" | "today" | "last7";

export default function VoicemailPage() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [expandedVoicemailId, setExpandedVoicemailId] = useState<number | null>(null);
    const [openMenuVoicemailId, setOpenMenuVoicemailId] = useState<number | null>(null);
    const [noteEditorVoicemailId, setNoteEditorVoicemailId] = useState<number | null>(null);
    const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});
    const [autoListenInFlight, setAutoListenInFlight] = useState<Record<number, boolean>>({});
    const [actionError, setActionError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);
    const [quickFilter, setQuickFilter] = useState<VoicemailQuickFilter>("all");
    const [isCompactLayout, setIsCompactLayout] = useState(() => window.innerWidth < 1120);

    const [audioBlobUrls, setAudioBlobUrls] = useState<Record<number, string>>({});
    const [audioLoadErrors, setAudioLoadErrors] = useState<Record<number, string>>({});
    const [audioLoadingIds, setAudioLoadingIds] = useState<Record<number, boolean>>({});
    const [pendingAutoPlayId, setPendingAutoPlayId] = useState<number | null>(null);

    const audioElementRefs = useRef<Record<number, HTMLAudioElement | null>>({});
    const { data: voicemails = [], error } = useAsyncData<VoicemailRecord[]>(() => fetchVoicemails(), [refreshKey]);

    const filteredVoicemails = voicemails.filter((voicemail) => {
        if (quickFilter === "all") {
            return true;
        }
        if (quickFilter === "new" || quickFilter === "listened" || quickFilter === "archived") {
            return voicemail.status === quickFilter;
        }

        const createdAt = new Date(voicemail.created_at);
        if (Number.isNaN(createdAt.getTime())) {
            return false;
        }

        const now = new Date();
        if (quickFilter === "today") {
            return createdAt.toDateString() === now.toDateString();
        }

        const sevenDaysAgo = new Date(now);
        sevenDaysAgo.setDate(now.getDate() - 7);
        return createdAt >= sevenDaysAgo;
    });

    const prevBlobUrls = useRef<Record<number, string>>({});
    useEffect(() => {
        const previous = prevBlobUrls.current;
        for (const [idText, url] of Object.entries(audioBlobUrls)) {
            const id = Number(idText);
            if (previous[id] && previous[id] !== url) {
                URL.revokeObjectURL(previous[id]);
            }
        }
        prevBlobUrls.current = audioBlobUrls;
    }, [audioBlobUrls]);

    useEffect(() => {
        return () => {
            for (const url of Object.values(prevBlobUrls.current)) {
                URL.revokeObjectURL(url);
            }
        };
    }, []);

    useEffect(() => {
        function onResize() {
            setIsCompactLayout(window.innerWidth < 1120);
        }

        window.addEventListener("resize", onResize);
        return () => {
            window.removeEventListener("resize", onResize);
        };
    }, []);

    useEffect(() => {
        function onDocumentClick(event: MouseEvent) {
            const target = event.target as HTMLElement | null;
            if (!target?.closest("[data-voicemail-menu]")) {
                setOpenMenuVoicemailId(null);
            }
        }

        function onEscape(event: KeyboardEvent) {
            if (event.key === "Escape") {
                setOpenMenuVoicemailId(null);
            }
        }

        document.addEventListener("mousedown", onDocumentClick);
        document.addEventListener("keydown", onEscape);
        return () => {
            document.removeEventListener("mousedown", onDocumentClick);
            document.removeEventListener("keydown", onEscape);
        };
    }, []);

    useEffect(() => {
        if (pendingAutoPlayId === null) {
            return;
        }
        if (expandedVoicemailId !== pendingAutoPlayId) {
            return;
        }
        if (!audioBlobUrls[pendingAutoPlayId]) {
            return;
        }
        const audio = audioElementRefs.current[pendingAutoPlayId];
        if (!audio) {
            return;
        }
        const playback = audio.play();
        if (playback && typeof playback.catch === "function") {
            void playback.catch(() => {
                // Browser autoplay restrictions can block scripted play.
            });
        }
        setPendingAutoPlayId(null);
    }, [pendingAutoPlayId, expandedVoicemailId, audioBlobUrls]);

    async function refresh() {
        setRefreshKey((current) => current + 1);
    }

    async function loadAudio(voicemailId: number): Promise<boolean> {
        if (audioBlobUrls[voicemailId]) {
            return true;
        }
        if (audioLoadingIds[voicemailId]) {
            return false;
        }

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
            return true;
        } catch (err) {
            const message = err instanceof Error ? err.message : "Could not load audio.";
            setAudioLoadErrors((current) => ({ ...current, [voicemailId]: message }));
            return false;
        } finally {
            setAudioLoadingIds((current) => ({ ...current, [voicemailId]: false }));
        }
    }

    function retryAudio(voicemailId: number) {
        void loadAudio(voicemailId);
    }

    async function ensureExpandedWithAudio(voicemail: VoicemailRecord, playWhenReady: boolean) {
        setExpandedVoicemailId(voicemail.id);
        if (!voicemail.recording_url) {
            setActionError("Recording audio not available yet.");
            return;
        }

        const alreadyLoaded = Boolean(audioBlobUrls[voicemail.id]);
        const loaded = alreadyLoaded || await loadAudio(voicemail.id);
        if (!loaded) {
            return;
        }

        if (playWhenReady) {
            setPendingAutoPlayId(voicemail.id);
        }
    }

    async function setStatus(voicemailId: number, status: "new" | "listened" | "archived") {
        try {
            setActionError(null);
            setActionMessage(null);
            setOpenMenuVoicemailId(null);
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
            setNoteEditorVoicemailId(null);
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
        if (!window.confirm("Delete this voicemail? This cannot be undone.")) {
            return;
        }
        try {
            setActionError(null);
            setActionMessage(null);
            setOpenMenuVoicemailId(null);
            await deleteVoicemail(voicemailId);
            if (expandedVoicemailId === voicemailId) {
                setExpandedVoicemailId(null);
                setNoteEditorVoicemailId(null);
            }
            setActionMessage("Voicemail deleted.");
            await refresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not delete voicemail");
        }
    }

    async function copyCallerNumber(callerNumber: string | null) {
        if (!callerNumber) {
            setActionError("Caller number is unknown for this voicemail.");
            return;
        }
        try {
            setActionError(null);
            setActionMessage(null);
            if (navigator.clipboard?.writeText) {
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
            setOpenMenuVoicemailId(null);
            setActionMessage("Caller number copied.");
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Could not copy caller number");
        }
    }

    function openNoteEditor(voicemailId: number) {
        setExpandedVoicemailId(voicemailId);
        setNoteEditorVoicemailId(voicemailId);
        setOpenMenuVoicemailId(null);
    }

    return (
        <section style={{ ...t.pageWrap, gap: "14px" }}>
            <PageHeader
                kicker="Communication"
                title="Voicemail Inbox"
                description="Compact inbox view with playback and contact actions."
                actions={<Link to="/settings" style={backLinkStyle}>Back to Settings</Link>}
            />

            <div style={{ ...t.formActionsRow, gap: "8px" }}>
                <button type="button" style={{ ...t.miniBtn, ...(quickFilter === "all" ? activeFilterStyle : null) }} onClick={() => setQuickFilter("all")}>All</button>
                <button type="button" style={{ ...t.miniBtn, ...(quickFilter === "new" ? activeFilterStyle : null) }} onClick={() => setQuickFilter("new")}>New</button>
                <button type="button" style={{ ...t.miniBtn, ...(quickFilter === "listened" ? activeFilterStyle : null) }} onClick={() => setQuickFilter("listened")}>Listened</button>
                <button type="button" style={{ ...t.miniBtn, ...(quickFilter === "archived" ? activeFilterStyle : null) }} onClick={() => setQuickFilter("archived")}>Done</button>
                <button type="button" style={{ ...t.miniBtn, ...(quickFilter === "today" ? activeFilterStyle : null) }} onClick={() => setQuickFilter("today")}>Today</button>
                <button type="button" style={{ ...t.miniBtn, ...(quickFilter === "last7" ? activeFilterStyle : null) }} onClick={() => setQuickFilter("last7")}>Last 7 days</button>
            </div>

            {actionError ? <div style={t.errorBanner}>{actionError}</div> : null}
            {actionMessage ? <div style={successBannerStyle}>{actionMessage}</div> : null}
            {error ? <div style={t.errorBanner}>{error}</div> : null}

            {filteredVoicemails.length === 0 ? (
                <SectionCard compact>
                    <p style={t.copy}>No voicemails for this filter. New messages will show up here.</p>
                </SectionCard>
            ) : (
                <div style={{ display: "grid", gap: "8px" }}>
                    {filteredVoicemails.map((voicemail) => {
                        const isExpanded = expandedVoicemailId === voicemail.id;
                        const isMenuOpen = openMenuVoicemailId === voicemail.id;
                        const isNoteEditorOpen = noteEditorVoicemailId === voicemail.id;
                        const fromLabel = `From: ${formatPhone(voicemail.caller_number)}`;
                        const lineLabel = `Line: ${formatPhone(voicemail.called_number)}`;
                        const receivedLabel = formatDeskDateTime(voicemail.created_at);
                        const durationLabel = formatDurationSeconds(voicemail.recording_duration_seconds);
                        const compactMeta = `${lineLabel} | ${receivedLabel} | ${durationLabel}`;

                        return (
                            <article key={voicemail.id} style={rowWrapStyle}>
                                <div style={isCompactLayout ? compactRowMainStyle : rowMainStyle}>
                                    <span style={{ ...statusChipStyle, ...statusStyles[voicemail.status as keyof typeof statusStyles] }}>
                                        {statusLabel[voicemail.status as keyof typeof statusLabel]}
                                    </span>

                                    <div style={fieldStyle}>{fromLabel}</div>
                                    {isCompactLayout ? <div style={compactMetaStyle}>{compactMeta}</div> : null}
                                    {!isCompactLayout ? <div style={fieldStyle}>{lineLabel}</div> : null}
                                    {!isCompactLayout ? <div style={fieldStyle}>{receivedLabel}</div> : null}
                                    {!isCompactLayout ? <div style={fieldStyle}>{durationLabel}</div> : null}

                                    <button
                                        type="button"
                                        style={playBtnStyle}
                                        onClick={() => void ensureExpandedWithAudio(voicemail, true)}
                                        disabled={!voicemail.recording_url}
                                    >
                                        Play
                                    </button>

                                    <div data-voicemail-menu style={menuWrapStyle}>
                                        <button
                                            type="button"
                                            aria-haspopup="menu"
                                            aria-expanded={isMenuOpen}
                                            aria-label={`More actions for voicemail ${voicemail.id}`}
                                            style={menuTriggerStyle}
                                            onClick={() => setOpenMenuVoicemailId((current) => (current === voicemail.id ? null : voicemail.id))}
                                        >
                                            ⋮
                                        </button>

                                        {isMenuOpen ? (
                                            <div role="menu" style={menuPanelStyle}>
                                                <button type="button" role="menuitem" style={menuItemStyle} onClick={() => void setStatus(voicemail.id, "listened")}>Mark listened</button>
                                                <button type="button" role="menuitem" style={menuItemStyle} onClick={() => void setStatus(voicemail.id, "archived")}>Mark done</button>
                                                <button type="button" role="menuitem" style={menuItemStyle} onClick={() => openNoteEditor(voicemail.id)}>{voicemail.notes ? "Add/Edit note" : "Add note"}</button>
                                                <button
                                                    type="button"
                                                    role="menuitem"
                                                    style={menuItemStyle}
                                                    onClick={() => void copyCallerNumber(voicemail.caller_number)}
                                                    disabled={!voicemail.caller_number}
                                                >
                                                    Copy caller number
                                                </button>
                                                <button type="button" role="menuitem" style={menuDeleteStyle} onClick={() => void removeVoicemail(voicemail.id)}>Delete</button>
                                            </div>
                                        ) : null}
                                    </div>
                                </div>

                                {isExpanded ? (
                                    <div style={expandedBodyStyle}>
                                        {voicemail.recording_url ? (
                                            audioBlobUrls[voicemail.id] ? (
                                                <audio
                                                    controls
                                                    style={audioPlayerStyle}
                                                    src={audioBlobUrls[voicemail.id]}
                                                    onPlay={() => void markListenedFromPlayback(voicemail)}
                                                    ref={(element) => {
                                                        audioElementRefs.current[voicemail.id] = element;
                                                    }}
                                                />
                                            ) : audioLoadErrors[voicemail.id] ? (
                                                <div style={{ display: "grid", gap: "6px" }}>
                                                    <div style={compactWarningStyle}>{audioLoadErrors[voicemail.id]}</div>
                                                    <button type="button" style={compactBtnStyle} onClick={() => retryAudio(voicemail.id)}>Retry</button>
                                                </div>
                                            ) : (
                                                <div style={{ ...t.meta, marginTop: 0 }}>{audioLoadingIds[voicemail.id] ? "Loading audio..." : "Audio pending..."}</div>
                                            )
                                        ) : (
                                            <div style={compactWarningStyle}>This voicemail is still processing. Try again in a few seconds.</div>
                                        )}

                                        {voicemail.notes ? <pre style={noteLogStyle}>{voicemail.notes}</pre> : null}

                                        {isNoteEditorOpen ? (
                                            <div style={{ display: "grid", gap: "6px" }}>
                                                <textarea
                                                    value={noteDrafts[voicemail.id] || ""}
                                                    onChange={(event) => setNoteDrafts((current) => ({ ...current, [voicemail.id]: event.target.value }))}
                                                    placeholder="Add follow-up note"
                                                    style={noteInputStyle}
                                                />
                                                <div style={{ ...t.formActionsRow, gap: "6px" }}>
                                                    <button type="button" style={compactPrimaryBtnStyle} onClick={() => void saveNote(voicemail.id)}>Save note</button>
                                                    <button type="button" style={compactBtnStyle} onClick={() => setNoteEditorVoicemailId(null)}>Cancel</button>
                                                </div>
                                            </div>
                                        ) : null}
                                    </div>
                                ) : null}
                            </article>
                        );
                    })}
                </div>
            )}
        </section>
    );
}

const rowWrapStyle: React.CSSProperties = {
    ...t.panel,
    padding: "10px 12px",
    borderRadius: "14px",
};

const rowMainStyle: React.CSSProperties = {
    display: "grid",
    gridTemplateColumns: "auto minmax(0, 1.2fr) minmax(0, 1fr) auto auto auto",
    gap: "8px 10px",
    alignItems: "center",
};

const compactRowMainStyle: React.CSSProperties = {
    display: "grid",
    gridTemplateColumns: "auto minmax(0, 1fr) auto auto",
    gap: "8px 10px",
    alignItems: "center",
};

const statusChipStyle: React.CSSProperties = {
    borderRadius: "999px",
    padding: "4px 9px",
    fontWeight: 700,
    fontSize: "0.72rem",
    border: "1px solid transparent",
    whiteSpace: "nowrap",
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

const fieldStyle: React.CSSProperties = {
    fontSize: "0.84rem",
    color: "#33453f",
    minWidth: 0,
    maxWidth: "100%",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
};

const compactMetaStyle: React.CSSProperties = {
    fontSize: "0.8rem",
    color: "#5f6d69",
    minWidth: 0,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
};

const playBtnStyle: React.CSSProperties = {
    ...t.miniBtn,
    fontWeight: 700,
};

const menuWrapStyle: React.CSSProperties = {
    position: "relative",
    marginLeft: "auto",
};

const menuTriggerStyle: React.CSSProperties = {
    ...t.miniBtn,
    minWidth: "34px",
    width: "34px",
    height: "34px",
    fontSize: "1rem",
    lineHeight: 1,
    padding: 0,
    display: "grid",
    placeItems: "center",
};

const menuPanelStyle: React.CSSProperties = {
    position: "absolute",
    top: "36px",
    right: 0,
    zIndex: 20,
    minWidth: "170px",
    background: "#ffffff",
    border: "1px solid rgba(29,43,40,0.16)",
    borderRadius: "10px",
    boxShadow: "0 12px 24px rgba(21, 40, 36, 0.18)",
    padding: "4px",
    display: "grid",
    gap: "2px",
};

const menuItemStyle: React.CSSProperties = {
    border: "none",
    background: "transparent",
    color: "#1d2b28",
    textAlign: "left",
    borderRadius: "8px",
    padding: "8px 10px",
    fontSize: "0.86rem",
    cursor: "pointer",
};

const menuDeleteStyle: React.CSSProperties = {
    ...menuItemStyle,
    marginTop: "2px",
    borderTop: "1px solid rgba(29,43,40,0.12)",
    borderRadius: "0 0 8px 8px",
    color: "#9b2c2c",
};

const expandedBodyStyle: React.CSSProperties = {
    marginTop: "8px",
    paddingTop: "8px",
    borderTop: "1px solid rgba(29,43,40,0.12)",
    display: "grid",
    gap: "8px",
};

const audioPlayerStyle: React.CSSProperties = {
    width: "100%",
    height: "34px",
};

const noteLogStyle: React.CSSProperties = {
    whiteSpace: "pre-wrap",
    background: "#f8f3ea",
    borderRadius: "10px",
    padding: "8px 10px",
    margin: 0,
    border: "1px solid rgba(29,43,40,0.12)",
    fontSize: "0.83rem",
    lineHeight: 1.4,
};

const noteInputStyle: React.CSSProperties = {
    ...t.input,
    minHeight: "68px",
    padding: "10px 12px",
    resize: "vertical",
    fontSize: "0.92rem",
};

const compactBtnStyle: React.CSSProperties = {
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

const compactWarningStyle: React.CSSProperties = {
    ...t.warning,
    padding: "8px 10px",
    fontSize: "0.84rem",
};

const successBannerStyle: React.CSSProperties = {
    ...t.warning,
    background: "#d1fae5",
    color: "#065f46",
    borderColor: "#a7f3d0",
};

const backLinkStyle: React.CSSProperties = {
    textDecoration: "none",
    borderRadius: "999px",
    border: "1px solid rgba(29,43,40,0.14)",
    background: "#ffffff",
    color: "#1d2b28",
    padding: "8px 12px",
    fontWeight: 700,
};

const activeFilterStyle: React.CSSProperties = {
    background: "#1f6657",
    color: "#ffffff",
    borderColor: "#1f6657",
};
