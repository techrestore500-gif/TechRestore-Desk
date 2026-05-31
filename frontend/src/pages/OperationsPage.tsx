import { Link } from "react-router-dom";

import { fetchDonors, fetchLoaners, fetchLowStockParts, type DonorDevice, type LoanerPhone, type Part } from "../api/tickets";
import { PageHeader, SectionCard, MetricTile } from "../components/PageChrome";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

export default function OperationsPage() {
    const { data: loaners = [] } = useAsyncData<LoanerPhone[]>(() => fetchLoaners(), []);
    const { data: donors = [] } = useAsyncData<DonorDevice[]>(() => fetchDonors(), []);
    const { data: lowStockParts = [] } = useAsyncData<Part[]>(() => fetchLowStockParts(), []);

    const checkedOutLoaners = loaners.filter((item) => item.status.toLowerCase() === "checked_out").length;
    const availableLoaners = loaners.filter((item) => item.status.toLowerCase() === "available").length;
    const activeDonors = donors.filter((item) => item.status.toLowerCase() !== "retired").length;

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Operations"
                title="Operations Hub"
                description="Use this workspace for inventory, loaners, donor devices, and reporting tools."
                actions={<Link to="/inventory" style={{ ...t.primaryBtn, textDecoration: "none" }}>Open Inventory</Link>}
            />

            <div style={t.detailGrid}>
                <MetricTile label="Low Stock Parts" value={String(lowStockParts.length)} hint="Needs reorder" />
                <MetricTile label="Loaners Checked Out" value={String(checkedOutLoaners)} hint="Active agreements" />
                <MetricTile label="Loaners Available" value={String(availableLoaners)} hint="Ready to assign" />
                <MetricTile label="Active Donors" value={String(activeDonors)} hint="Harvest candidates" />
            </div>

            <SectionCard title="Operational Workspaces" description="Open the exact surface you need without keeping all pages in primary nav.">
                <div style={{ ...t.detailGrid, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                    <QuickLink
                        title="Inventory"
                        copy="Parts stock, low-stock risks, and movement tracking."
                        to="/inventory"
                    />
                    <QuickLink
                        title="Loaners"
                        copy="Checkout, return, and lifecycle tracking."
                        to="/loaners"
                    />
                    <QuickLink
                        title="Donors"
                        copy="Donor intake and part harvest workflow."
                        to="/donors"
                    />
                    <QuickLink
                        title="Reports"
                        copy="Revenue, throughput, and performance snapshots."
                        to="/reports"
                    />
                </div>
            </SectionCard>

            <SectionCard title="Triage Notes" compact tone="soft">
                <div style={{ display: "grid", gap: "8px" }}>
                    <div style={t.meta}>Use Queue for active repair status movement and assignment.</div>
                    <div style={t.meta}>Use Hours for technician time logging and summaries.</div>
                    <div style={t.meta}>Use Settings for workflow rules, Twilio, templates, and backups.</div>
                </div>
            </SectionCard>
        </section>
    );
}

function QuickLink({ title, copy, to }: { title: string; copy: string; to: string }) {
    return (
        <Link to={to} style={quickLinkStyle}>
            <strong style={{ color: "#132f29" }}>{title}</strong>
            <span style={{ ...t.meta, marginTop: "4px" }}>{copy}</span>
        </Link>
    );
}

const quickLinkStyle = {
    ...t.panel,
    textDecoration: "none",
    display: "grid",
    gap: "4px",
    padding: "14px",
    borderRadius: "14px",
};
