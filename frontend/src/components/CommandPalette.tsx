import { useMemo } from "react";
import { useNavigate } from "react-router-dom";

import { useGlobalSearchQuery } from "../hooks/queries/useGlobalSearchQuery";
import { useUiStore } from "../store/uiStore";

export function CommandPalette() {
    const navigate = useNavigate();
    const isOpen = useUiStore((state) => state.commandPaletteOpen);
    const query = useUiStore((state) => state.commandPaletteQuery);
    const setQuery = useUiStore((state) => state.setCommandPaletteQuery);
    const setOpen = useUiStore((state) => state.setCommandPaletteOpen);

    const { data, isLoading } = useGlobalSearchQuery(query, isOpen);

    const items = useMemo(() => data ?? [], [data]);

    if (!isOpen) {
        return null;
    }

    return (
        <div style={overlayStyle} onClick={() => setOpen(false)}>
            <div style={modalStyle} onClick={(event) => event.stopPropagation()}>
                <input
                    autoFocus
                    placeholder="Search tickets, parts, donors, loaners..."
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    style={searchStyle}
                />
                <div style={{ maxHeight: "50vh", overflowY: "auto", marginTop: "10px" }}>
                    {isLoading ? <p style={{ margin: 0 }}>Searching...</p> : null}
                    {!isLoading && items.length === 0 ? <p style={{ margin: 0, color: "#4a6492" }}>No results</p> : null}
                    {items.map((item) => (
                        <button
                            key={`${item.type}:${item.id}`}
                            type="button"
                            style={itemStyle}
                            onClick={() => {
                                setOpen(false);
                                navigate(item.path);
                            }}
                        >
                            <strong>{item.label}</strong>
                            <span style={{ color: "#4a6492" }}>{item.subtitle}</span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

const overlayStyle = {
    position: "fixed" as const,
    inset: 0,
    backgroundColor: "rgba(11, 22, 48, 0.42)",
    display: "grid",
    placeItems: "start center",
    paddingTop: "10vh",
    zIndex: 100,
};

const modalStyle = {
    width: "min(760px, 92vw)",
    background: "#fff",
    borderRadius: "14px",
    border: "1px solid #c5d7fb",
    padding: "12px",
    boxShadow: "0 24px 44px rgba(21, 44, 92, 0.24)",
};

const searchStyle = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "10px",
    border: "1px solid #9fb7ea",
};

const itemStyle = {
    width: "100%",
    textAlign: "left" as const,
    display: "grid",
    gap: "2px",
    border: "1px solid #e4ebfa",
    borderRadius: "8px",
    marginBottom: "6px",
    padding: "10px",
    background: "#fff",
    cursor: "pointer",
};
