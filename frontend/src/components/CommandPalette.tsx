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
                    {!isLoading && items.length === 0 ? <p style={{ margin: 0, color: "#60756f" }}>No results</p> : null}
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
                            <span style={{ color: "#60756f" }}>{item.subtitle}</span>
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
    backgroundColor: "rgba(8, 18, 16, 0.35)",
    display: "grid",
    placeItems: "start center",
    paddingTop: "10vh",
    zIndex: 100,
};

const modalStyle = {
    width: "min(760px, 92vw)",
    background: "#fff",
    borderRadius: "14px",
    border: "1px solid #d7e0df",
    padding: "12px",
    boxShadow: "0 24px 44px rgba(19, 47, 41, 0.24)",
};

const searchStyle = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "10px",
    border: "1px solid #bfd0cb",
};

const itemStyle = {
    width: "100%",
    textAlign: "left" as const,
    display: "grid",
    gap: "2px",
    border: "1px solid #eef3f1",
    borderRadius: "8px",
    marginBottom: "6px",
    padding: "10px",
    background: "#fff",
    cursor: "pointer",
};
