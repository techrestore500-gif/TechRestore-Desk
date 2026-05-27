import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DataTable } from "./DataTable";

type Row = { id: number; name: string; qty: number };

const rows: Row[] = [
    { id: 1, name: "B", qty: 2 },
    { id: 2, name: "A", qty: 5 },
    { id: 3, name: "C", qty: 1 },
];

describe("DataTable", () => {
    it("sorts and paginates rows", () => {
        const onPageChange = vi.fn();

        render(
            <DataTable
                rows={rows}
                columns={[
                    {
                        key: "name",
                        header: "Name",
                        sortable: true,
                        sortValue: (row) => row.name,
                        render: (row) => row.name,
                    },
                    {
                        key: "qty",
                        header: "Qty",
                        sortable: true,
                        sortValue: (row) => row.qty,
                        render: (row) => row.qty,
                    },
                ]}
                page={1}
                pageSize={2}
                onPageChange={onPageChange}
            />
        );

        fireEvent.click(screen.getByText("Name"));
        expect(screen.getByText("A")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Next" }));
        expect(onPageChange).toHaveBeenCalledWith(2);
    });
});
