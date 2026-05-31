import { ReactNode, useMemo, useState } from "react";

type Column<T> = {
    key: string;
    header: string;
    sortable?: boolean;
    render: (row: T) => ReactNode;
    sortValue?: (row: T) => string | number | null;
};

type BulkAction<T> = {
    key: string;
    label: string;
    onClick: (rows: T[]) => void;
};

export function DataTable<T extends { id: number | string }>({
    rows,
    columns,
    page,
    pageSize,
    onPageChange,
    rowActions,
    bulkActions,
}: {
    rows: T[];
    columns: Column<T>[];
    page: number;
    pageSize: number;
    onPageChange: (page: number) => void;
    rowActions?: (row: T) => ReactNode;
    bulkActions?: BulkAction<T>[];
}) {
    const [sortBy, setSortBy] = useState<string | null>(null);
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set());

    const sortedRows = useMemo(() => {
        if (!sortBy) {
            return rows;
        }

        const column = columns.find((item) => item.key === sortBy);
        if (!column?.sortValue) {
            return rows;
        }

        return [...rows].sort((left, right) => {
            const a = column.sortValue?.(left);
            const b = column.sortValue?.(right);
            const safeA = a ?? "";
            const safeB = b ?? "";
            if (safeA < safeB) {
                return sortDirection === "asc" ? -1 : 1;
            }
            if (safeA > safeB) {
                return sortDirection === "asc" ? 1 : -1;
            }
            return 0;
        });
    }, [columns, rows, sortBy, sortDirection]);

    const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
    const currentPage = Math.min(page, totalPages);
    const startIndex = (currentPage - 1) * pageSize;
    const pagedRows = sortedRows.slice(startIndex, startIndex + pageSize);

    const selectedRows = rows.filter((row) => selectedIds.has(row.id));
    const hasBulkActions = Boolean(bulkActions && bulkActions.length > 0);
    const hasRowActions = Boolean(rowActions);
    const minTableWidth = Math.max(980, columns.length * 160 + (hasBulkActions ? 70 : 0) + (hasRowActions ? 170 : 0));

    const toggleSort = (column: Column<T>) => {
        if (!column.sortable) {
            return;
        }
        if (sortBy === column.key) {
            setSortDirection((dir) => (dir === "asc" ? "desc" : "asc"));
            return;
        }
        setSortBy(column.key);
        setSortDirection("asc");
    };

    const toggleRowSelection = (rowId: string | number) => {
        setSelectedIds((prev) => {
            const next = new Set(prev);
            if (next.has(rowId)) {
                next.delete(rowId);
            } else {
                next.add(rowId);
            }
            return next;
        });
    };

    return (
        <div style={{ display: "grid", gap: "8px" }}>
            {bulkActions && bulkActions.length > 0 ? (
                <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                    <strong>{selectedRows.length} selected</strong>
                    {bulkActions.map((action) => (
                        <button
                            key={action.key}
                            type="button"
                            disabled={selectedRows.length === 0}
                            onClick={() => action.onClick(selectedRows)}
                            style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid #bfd0cb", cursor: "pointer" }}
                        >
                            {action.label}
                        </button>
                    ))}
                </div>
            ) : null}
            <div style={{ overflowX: "auto", border: "1px solid #d7e0df", borderRadius: "12px" }}>
                <table style={{ width: "100%", minWidth: `${minTableWidth}px`, borderCollapse: "collapse", backgroundColor: "#fff" }}>
                    <thead style={{ backgroundColor: "#1f4a41", color: "#f7f5ee" }}>
                        <tr>
                            {hasBulkActions ? <th style={thStyle}>Select</th> : null}
                            {columns.map((column) => (
                                <th
                                    key={column.key}
                                    style={{ ...thStyle, cursor: column.sortable ? "pointer" : "default" }}
                                    onClick={() => toggleSort(column)}
                                >
                                    {column.header}
                                    {sortBy === column.key ? (sortDirection === "asc" ? " ▲" : " ▼") : ""}
                                </th>
                            ))}
                            {hasRowActions ? <th style={thStyle}>Actions</th> : null}
                        </tr>
                    </thead>
                    <tbody>
                        {pagedRows.length === 0 ? (
                            <tr>
                                <td colSpan={columns.length + (hasRowActions ? 1 : 0) + (hasBulkActions ? 1 : 0)} style={tdStyle}>
                                    No records.
                                </td>
                            </tr>
                        ) : (
                            pagedRows.map((row) => (
                                <tr key={String(row.id)}>
                                    {hasBulkActions ? (
                                        <td style={tdStyle}>
                                            <input
                                                type="checkbox"
                                                checked={selectedIds.has(row.id)}
                                                onChange={() => toggleRowSelection(row.id)}
                                            />
                                        </td>
                                    ) : null}
                                    {columns.map((column) => (
                                        <td key={column.key} style={tdStyle}>
                                            {column.render(row)}
                                        </td>
                                    ))}
                                    {rowActions ? <td style={tdStyle}>{rowActions(row)}</td> : null}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                <span>
                    Page {currentPage} / {totalPages}
                </span>
                <div style={{ display: "flex", gap: "8px" }}>
                    <button type="button" onClick={() => onPageChange(Math.max(1, currentPage - 1))} disabled={currentPage <= 1}>
                        Prev
                    </button>
                    <button type="button" onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))} disabled={currentPage >= totalPages}>
                        Next
                    </button>
                </div>
            </div>
        </div>
    );
}

const thStyle = {
    padding: "10px",
    textAlign: "left" as const,
    borderBottom: "1px solid rgba(255,255,255,0.22)",
    fontSize: "0.9rem",
    whiteSpace: "nowrap" as const,
    overflowWrap: "normal" as const,
    wordBreak: "normal" as const,
};

const tdStyle = {
    padding: "10px",
    borderBottom: "1px solid #ebf1ef",
    verticalAlign: "top" as const,
    overflowWrap: "normal" as const,
    wordBreak: "normal" as const,
};
