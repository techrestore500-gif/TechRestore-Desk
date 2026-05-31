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
                description="Run supply, loaner, and donor workflows from one coordinated control plane."
                actions={
                    <div style={{ ...t.formActionsRow, gap: "8px" }}>
                        <Link to="/inventory" style={{ ...t.primaryBtn, textDecoration: "none" }}>Inventory</Link>
                        <Link to="/reports" style={{ ...t.secondaryBtn, textDecoration: "none" }}>Reports</Link>
                    </div>
                }
            />

            <div style={t.detailGrid}>
                <MetricTile label="Low Stock Parts" value={String(lowStockParts.length)} hint="Needs reorder" />
                <MetricTile label="Loaners Checked Out" value={String(checkedOutLoaners)} hint="Active agreements" />
                <MetricTile label="Loaners Available" value={String(availableLoaners)} hint="Ready to assign" />
                <MetricTile label="Active Donors" value={String(activeDonors)} hint="Harvest candidates" />
            </div>

            <div style={operationsGridStyle}>
                <SectionCard title="Dispatch Lane" description="Where next decisions happen during live service flow.">
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <QuickLink title="Queue" copy="Move repairs through active statuses." to="/queue" />
                        <QuickLink title="Hours" copy="Track technician time and labor view." to="/hours" />
                        <QuickLink title="Tickets" copy="Open full ticket board and customer context." to="/tickets" />
                    </div>
                </SectionCard>

                <SectionCard title="Asset Lane" description="Manage physical assets and replacement strategy." tone="soft">
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <QuickLink title="Inventory" copy="Parts stock, low-stock risks, and movement tracking." to="/inventory" />
                        <QuickLink title="Loaners" copy="Checkout, return, and lifecycle tracking." to="/loaners" />
                        <QuickLink title="Donors" copy="Donor intake and part-harvest workflow." to="/donors" />
                    </div>
                </SectionCard>

                <SectionCard title="Strategy Lane" description="Business-level visibility and control surfaces." tone="accent">
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <QuickLink title="Reports" copy="Revenue, throughput, and performance snapshots." to="/reports" />
                        <QuickLink title="Settings" copy="Workflow rules, templates, Twilio, and backups." to="/settings" />
                        <QuickLink title="Voicemail" copy="Manage missed calls and callback backlog." to="/voicemail" />
                    </div>
                </SectionCard>
            </div>

            <SectionCard title="Operating Notes" compact tone="soft">
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
            <strong style={{ color: "#133943" }}>{title}</strong>
            <span style={{ ...t.meta, marginTop: "4px" }}>{copy}</span>
        </Link>
    );
}

const quickLinkStyle = {
    ...t.panel,
    textDecoration: "none",
    display: "grid",
    gap: "4px",
    padding: "12px 13px",
    borderRadius: "14px",
};

const operationsGridStyle = {
    display: "grid",
    gap: "12px",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
};
