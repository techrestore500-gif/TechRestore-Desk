import { useState } from 'react';

import { fetchReportSummary, type ReportSummary } from '../api/tickets';
import { useAsyncData } from '../hooks/useAsyncData';
import { MetricTile, PageHeader, SectionCard } from '../components/PageChrome';
import * as t from '../styles/theme';

function todayIsoDate() {
    return new Date().toISOString().slice(0, 10);
}

function isoDateOffset(days: number) {
    const next = new Date();
    next.setDate(next.getDate() + days);
    return next.toISOString().slice(0, 10);
}

export default function ReportsPage() {
    const [filters, setFilters] = useState({
        startDate: todayIsoDate(),
        endDate: todayIsoDate(),
        technician: '',
        repairCategory: '',
    });
    const [appliedFilters, setAppliedFilters] = useState(filters);

    const { data: summary, loading, error } = useAsyncData<ReportSummary>(
        () => fetchReportSummary({
            startDate: appliedFilters.startDate,
            endDate: appliedFilters.endDate,
            technician: appliedFilters.technician || undefined,
            repairCategory: appliedFilters.repairCategory || undefined,
        }),
        [appliedFilters.startDate, appliedFilters.endDate, appliedFilters.technician, appliedFilters.repairCategory]
    );

    const availableTechnicians = summary?.available_technicians ?? [];
    const availableRepairCategories = summary?.available_repair_categories ?? [];

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Admin"
                title="Reports"
                description="Repairs, revenue, and labor snapshots for a selected date range."
            />

            <SectionCard title="Filters" compact>
                <div style={{ ...t.formActionsRow, gap: '8px', marginBottom: '10px' }}>
                    <button type="button" style={t.miniBtn} onClick={() => setFilters((current) => ({ ...current, startDate: todayIsoDate(), endDate: todayIsoDate() }))}>Today</button>
                    <button type="button" style={t.miniBtn} onClick={() => setFilters((current) => ({ ...current, startDate: isoDateOffset(-6), endDate: todayIsoDate() }))}>This week</button>
                    <button type="button" style={t.miniBtn} onClick={() => setFilters((current) => ({ ...current, startDate: isoDateOffset(-29), endDate: todayIsoDate() }))}>This month</button>
                    <button type="button" style={t.miniBtn} onClick={() => setFilters((current) => ({ ...current, startDate: '', endDate: '' }))}>Custom</button>
                </div>
                <div style={t.fieldGrid}>
                    <label style={t.label}>
                        <span>Start date</span>
                        <input
                            type="date"
                            value={filters.startDate}
                            onChange={(event) => setFilters((current) => ({ ...current, startDate: event.target.value }))}
                            style={t.input}
                        />
                    </label>
                    <label style={t.label}>
                        <span>End date</span>
                        <input
                            type="date"
                            value={filters.endDate}
                            onChange={(event) => setFilters((current) => ({ ...current, endDate: event.target.value }))}
                            style={t.input}
                        />
                    </label>
                    <label style={t.label}>
                        <span>Technician</span>
                        <select
                            value={filters.technician}
                            onChange={(event) => setFilters((current) => ({ ...current, technician: event.target.value }))}
                            style={t.input}
                        >
                            <option value="">All technicians</option>
                            {availableTechnicians.map((item) => (
                                <option key={item} value={item}>{item}</option>
                            ))}
                        </select>
                    </label>
                    <label style={t.label}>
                        <span>Repair category</span>
                        <select
                            value={filters.repairCategory}
                            onChange={(event) => setFilters((current) => ({ ...current, repairCategory: event.target.value }))}
                            style={t.input}
                        >
                            <option value="">All repair categories</option>
                            {availableRepairCategories.map((item) => (
                                <option key={item} value={item}>{item}</option>
                            ))}
                        </select>
                    </label>
                </div>
                <button
                    type="button"
                    style={{ ...t.primaryBtn, marginTop: '12px' }}
                    onClick={() => setAppliedFilters(filters)}
                >
                    Apply filters
                </button>
                {error ? <p style={{ ...t.copy, color: '#9b2c2c' }}>{error}</p> : null}
            </SectionCard>

            {loading && !summary ? <SectionCard><p>Loading report…</p></SectionCard> : null}

            {summary ? (
                <>
                    <div style={t.detailGrid}>
                        <MetricTile label="Created tickets" value={String(summary.created_tickets_count)} />
                        <MetricTile label="Closed tickets" value={String(summary.closed_tickets_count)} />
                        <MetricTile label="Revenue" value={`$${summary.total_revenue.toFixed(2)}`} />
                        <MetricTile label="Hours logged" value={String(summary.total_hours)} />
                        <MetricTile label="Avg closed ticket" value={`$${summary.average_closed_ticket_revenue.toFixed(2)}`} />
                        <MetricTile label="Revenue / hour" value={`$${summary.revenue_per_hour.toFixed(2)}`} />
                    </div>

                    <div style={t.detailGrid}>
                        <SectionCard title="Technician breakdown" compact>
                            {summary.technician_breakdown.length === 0 ? (
                                <p style={t.copy}>No technician activity matched the current filters.</p>
                            ) : (
                                <div style={{ display: 'grid', gap: '10px' }}>
                                    {summary.technician_breakdown.map((item) => (
                                        <div key={item.technician} style={t.subCard}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                                <strong>{item.technician}</strong>
                                                <span style={t.meta}>${item.total_revenue.toFixed(2)} revenue</span>
                                            </div>
                                            <div style={{ ...t.meta, marginTop: '6px' }}>
                                                {item.total_hours.toFixed(2)} hours · {item.tickets_worked} tickets worked · {item.closed_tickets_count} closed
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </SectionCard>

                        <SectionCard title="Repair category breakdown" compact>
                            {summary.repair_category_breakdown.length === 0 ? (
                                <p style={t.copy}>No repair actions matched the current filters.</p>
                            ) : (
                                <div style={{ display: 'grid', gap: '10px' }}>
                                    {summary.repair_category_breakdown.map((item) => (
                                        <div key={item.repair_category} style={t.subCard}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                                <strong>{item.repair_category}</strong>
                                                <span style={t.meta}>${item.total_final_price.toFixed(2)}</span>
                                            </div>
                                            <div style={{ ...t.meta, marginTop: '6px' }}>
                                                {item.action_count} actions · {item.ticket_count} tickets
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </SectionCard>
                    </div>
                </>
            ) : null}
        </section>
    );
}
