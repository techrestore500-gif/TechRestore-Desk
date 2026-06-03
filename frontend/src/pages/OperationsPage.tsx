import { Link } from "react-router-dom";

import { fetchLowStockParts, type Part } from "../api/inventory";
import { PageHeader, SectionCard, MetricTile } from "../components/PageChrome";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

export default function OperationsPage() {
    const { data: lowStockParts = [] } = useAsyncData<Part[]>(() => fetchLowStockParts(), []);

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Shop Tools"
                title="Shop Tools"
                description="Quick access to inventory and admin reporting tasks."
                actions={
                    <div style={{ ...t.formActionsRow, gap: "8px" }}>
                        <Link to="/inventory" style={{ ...t.primaryBtn, textDecoration: "none" }}>Inventory</Link>
                        <Link to="/reports" style={{ ...t.secondaryBtn, textDecoration: "none" }}>Reports</Link>
                    </div>
                }
            />

            <div style={t.detailGrid}>
                <MetricTile label="Low Stock Parts" value={String(lowStockParts.length)} hint="Needs reorder" />
            </div>

            <div style={operationsGridStyle}>
                <SectionCard title="Repair Flow" description="Common desk workflows during active repair work.">
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <QuickLink title="Dashboard" copy="Start from the main work overview and recent repair activity." to="/" />
                        <QuickLink title="Tickets" copy="Open full ticket board and customer context." to="/tickets" />
                    </div>
                </SectionCard>

                <SectionCard title="Assets" description="Manage inventory stock and part levels." tone="soft">
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <QuickLink title="Inventory" copy="Parts stock, low-stock risks, and movement tracking." to="/inventory" />
                    </div>
                </SectionCard>

                <SectionCard title="Admin" description="Reporting, settings, and voicemail review." tone="accent">
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <QuickLink title="Reports" copy="Revenue, throughput, and performance snapshots." to="/reports" />
                        <QuickLink title="Settings" copy="Workflow rules, templates, Twilio, and backups." to="/settings" />
                        <QuickLink title="Voicemail" copy="Manage missed calls and callback backlog." to="/voicemail" />
                    </div>
                </SectionCard>
            </div>

            <SectionCard title="Operating Notes" compact tone="soft">
                <div style={{ display: "grid", gap: "8px" }}>
                    <div style={t.meta}>Keep daily flow in Dashboard, New Repair, Tickets, and Voicemail.</div>
                    <div style={t.meta}>Use Inventory and Reports for supply and operational visibility.</div>
                    <div style={t.meta}>Use Settings for Twilio, templates, workflow policy, and backups.</div>
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
