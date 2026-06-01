import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
    clockIn,
    clockOut,
    fetchActiveClockSession,
    fetchHours,
    fetchHoursSummary,
    logHours,
    type HoursClockSession,
    type HoursLog,
    type HoursSummary,
} from '../api/hours';
import { useAsyncData } from '../hooks/useAsyncData';
import { InlineState, PageHeader, SectionCard } from '../components/PageChrome';
import * as t from '../styles/theme';
import { LoadingSpinner } from '../components/LoadingSpinner';

const DEFAULT_TECHNICIAN = 'Mattis';

function loadRoster(): string[] {
    try {
        const raw = localStorage.getItem('techRestore.techRoster');
        if (raw) {
            const parsed = JSON.parse(raw) as string[];
            return parsed.length > 0 ? parsed : [DEFAULT_TECHNICIAN];
        }

        const legacyRaw = localStorage.getItem('tag.techRoster');
        if (legacyRaw) {
            localStorage.setItem('techRestore.techRoster', legacyRaw);
            const parsed = JSON.parse(legacyRaw) as string[];
            return parsed.length > 0 ? parsed : [DEFAULT_TECHNICIAN];
        }

        return [DEFAULT_TECHNICIAN];
    } catch {
        return [DEFAULT_TECHNICIAN];
    }
}

function todayIsoDate() {
    return new Date().toISOString().split('T')[0];
}

function formatDate(value: string) {
    return new Date(value).toLocaleDateString();
}

function formatDateTime(value: string) {
    return new Date(value).toLocaleString();
}

export function HoursPage() {
    const [roster] = useState<string[]>(() => loadRoster());
    const defaultTechnician = roster[0] ?? DEFAULT_TECHNICIAN;
    const [refreshKey, setRefreshKey] = useState(0);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [saving, setSaving] = useState<'clock-in' | 'clock-out' | 'manual' | null>(null);

    const [technician, setTechnician] = useState(defaultTechnician);
    const [clockTicketId, setClockTicketId] = useState('');
    const [clockDescription, setClockDescription] = useState('');
    const [manualWorkDate, setManualWorkDate] = useState(todayIsoDate());
    const [manualHoursWorked, setManualHoursWorked] = useState('1');
    const [manualWorkDescription, setManualWorkDescription] = useState('');
    const [manualTicketId, setManualTicketId] = useState('');

    const [filterStartDate, setFilterStartDate] = useState('');
    const [filterEndDate, setFilterEndDate] = useState('');
    const [filterTechnician, setFilterTechnician] = useState(defaultTechnician);
    const [appliedStartDate, setAppliedStartDate] = useState('');
    const [appliedEndDate, setAppliedEndDate] = useState('');
    const [appliedTechnician, setAppliedTechnician] = useState(defaultTechnician);

    useEffect(() => {
        if (!roster.includes(technician)) {
            setTechnician(defaultTechnician);
        }
        if (!roster.includes(filterTechnician)) {
            setFilterTechnician(defaultTechnician);
            setAppliedTechnician(defaultTechnician);
        }
    }, [defaultTechnician, filterTechnician, roster, technician]);

    const { data, loading, error } = useAsyncData(async () => {
        const [hoursData, summaryData] = await Promise.all([
            fetchHours(appliedStartDate || undefined, appliedEndDate || undefined, appliedTechnician || undefined),
            fetchHoursSummary(appliedStartDate || undefined, appliedEndDate || undefined, appliedTechnician || undefined),
        ]);
        return {
            hours: hoursData,
            summary: summaryData,
        };
    }, [appliedStartDate, appliedEndDate, appliedTechnician, refreshKey]);

    const { data: activeSession } = useAsyncData<HoursClockSession | null>(
        () => fetchActiveClockSession(technician),
        [technician, refreshKey]
    );

    const hours: HoursLog[] = data?.hours ?? [];
    const summary: HoursSummary | null = data?.summary ?? null;
    const visibleError = submitError ?? error;

    function refreshData() {
        setRefreshKey((current) => current + 1);
    }

    async function handleClockIn() {
        try {
            setSaving('clock-in');
            setSubmitError(null);
            await clockIn({
                technician,
                ticket_id: clockTicketId ? Number(clockTicketId) : undefined,
                work_description: clockDescription || undefined,
            });
            refreshData();
        } catch (err) {
            setSubmitError(err instanceof Error ? err.message : 'Failed to clock in');
        } finally {
            setSaving(null);
        }
    }

    async function handleClockOut() {
        try {
            setSaving('clock-out');
            setSubmitError(null);
            await clockOut({
                technician,
                ticket_id: clockTicketId ? Number(clockTicketId) : undefined,
                work_description: clockDescription || undefined,
            });
            setClockTicketId('');
            setClockDescription('');
            refreshData();
        } catch (err) {
            setSubmitError(err instanceof Error ? err.message : 'Failed to clock out');
        } finally {
            setSaving(null);
        }
    }

    async function handleAddHours(event: React.FormEvent) {
        event.preventDefault();
        if (!technician || !manualWorkDate || !manualHoursWorked) {
            setSubmitError('Please fill in technician, date, and hours.');
            return;
        }

        try {
            setSaving('manual');
            setSubmitError(null);
            await logHours({
                technician,
                work_date: manualWorkDate,
                hours_worked: Number(manualHoursWorked),
                work_description: manualWorkDescription || undefined,
                ticket_id: manualTicketId ? Number(manualTicketId) : undefined,
            });
            setManualHoursWorked('1');
            setManualWorkDescription('');
            setManualTicketId('');
            refreshData();
        } catch (err) {
            setSubmitError(err instanceof Error ? err.message : 'Failed to log hours');
        } finally {
            setSaving(null);
        }
    }

    function handleFilter(event: React.FormEvent) {
        event.preventDefault();
        setAppliedStartDate(filterStartDate);
        setAppliedEndDate(filterEndDate);
        setAppliedTechnician(filterTechnician);
        refreshData();
    }

    function handleResetFilters() {
        setFilterStartDate('');
        setFilterEndDate('');
        setFilterTechnician(defaultTechnician);
        setAppliedStartDate('');
        setAppliedEndDate('');
        setAppliedTechnician(defaultTechnician);
        refreshData();
    }

    const totalHours = summary?.total_hours ?? 0;
    const technicianBreakdown = summary ? Object.entries(summary.by_technician) : [];
    const activeTechnicians = summary ? Object.keys(summary.by_technician).length : 0;
    const latestEntryDate = hours.length > 0 ? formatDate(hours[0].work_date) : 'No entries yet';
    const logCountLabel = `${hours.length} ${hours.length === 1 ? 'entry' : 'entries'}`;
    const activeSessionElapsed = activeSession ? `${activeSession.elapsed_hours.toFixed(2)}h` : '0.00h';
    const activeTicket = activeSession?.ticket_id ? `#${activeSession.ticket_id}` : 'None';
    const appliedRangeLabel = appliedStartDate || appliedEndDate
        ? `${appliedStartDate || 'Start'} -> ${appliedEndDate || 'Now'}`
        : 'All time';

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Time Tracking"
                title="Hours"
                description="Control live sessions, corrections, and reporting from one operations board."
            />

            {visibleError ? <InlineState tone="error">{visibleError}</InlineState> : null}

            <section
                style={{
                    ...t.panel,
                    padding: '20px',
                    background: 'linear-gradient(120deg, rgba(12,57,66,0.94) 0%, rgba(22,103,99,0.9) 45%, rgba(241,174,77,0.86) 100%)',
                    color: '#f5fffd',
                    border: '1px solid rgba(9,38,47,0.25)',
                }}
            >
                <div style={{ display: 'grid', gap: '15px', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
                    <div style={{ borderRadius: '16px', background: 'rgba(255,255,255,0.13)', padding: '14px', border: '1px solid rgba(255,255,255,0.22)' }}>
                        <div style={{ fontSize: '0.74rem', letterSpacing: '0.09em', textTransform: 'uppercase', opacity: 0.85 }}>Total Time</div>
                        <div style={{ fontSize: '1.8rem', fontWeight: 800, lineHeight: 1.05, marginTop: '6px' }}>{totalHours}h</div>
                        <div style={{ marginTop: '5px', fontSize: '0.86rem', opacity: 0.85 }}>Total: {totalHours} hours</div>
                    </div>
                    <div style={{ borderRadius: '16px', background: 'rgba(255,255,255,0.13)', padding: '14px', border: '1px solid rgba(255,255,255,0.22)' }}>
                        <div style={{ fontSize: '0.74rem', letterSpacing: '0.09em', textTransform: 'uppercase', opacity: 0.85 }}>Clock State</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, marginTop: '8px' }}>{activeSession ? 'Clocked In' : 'Clocked Out'}</div>
                        <div style={{ marginTop: '4px', fontSize: '0.86rem', opacity: 0.85 }}>Elapsed {activeSessionElapsed}</div>
                    </div>
                    <div style={{ borderRadius: '16px', background: 'rgba(255,255,255,0.13)', padding: '14px', border: '1px solid rgba(255,255,255,0.22)' }}>
                        <div style={{ fontSize: '0.74rem', letterSpacing: '0.09em', textTransform: 'uppercase', opacity: 0.85 }}>Current Ticket</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, marginTop: '8px' }}>{activeTicket}</div>
                        <div style={{ marginTop: '4px', fontSize: '0.86rem', opacity: 0.85 }}>{activeSession?.work_description || 'No ticket note yet'}</div>
                    </div>
                    <div style={{ borderRadius: '16px', background: 'rgba(255,255,255,0.13)', padding: '14px', border: '1px solid rgba(255,255,255,0.22)' }}>
                        <div style={{ fontSize: '0.74rem', letterSpacing: '0.09em', textTransform: 'uppercase', opacity: 0.85 }}>Filter Window</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: '8px' }}>{appliedRangeLabel}</div>
                        <div style={{ marginTop: '4px', fontSize: '0.86rem', opacity: 0.85 }}>{logCountLabel} · {activeTechnicians} techs</div>
                    </div>
                </div>
            </section>

            <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'minmax(280px, 1fr) minmax(280px, 1fr)' }}>
                <section
                    style={{
                        ...t.panel,
                        padding: '18px',
                        background: 'linear-gradient(145deg, rgba(255,255,255,0.95) 0%, rgba(232,248,245,0.9) 100%)',
                        borderTop: '5px solid #128377',
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'baseline', flexWrap: 'wrap' }}>
                        <h3 style={{ margin: 0 }}>Live Session Control</h3>
                        <span style={{ color: '#2f5f63', fontSize: '0.86rem' }}>{activeSession ? `Started ${formatDateTime(activeSession.clocked_in_at)}` : 'No active session right now'}</span>
                    </div>
                    <p style={{ ...t.copy, marginTop: '8px', marginBottom: '12px' }}>Run active timing from here and convert the session into history with one click.</p>
                    <div style={t.fieldGrid}>
                        <label style={t.label}>
                            <span>Technician</span>
                            <input value={technician} onChange={(event) => setTechnician(event.target.value)} style={t.input} list="tech-roster" />
                            <datalist id="tech-roster">
                                {roster.map((name) => <option key={name} value={name} />)}
                            </datalist>
                        </label>
                        <label style={t.label}>
                            <span>Ticket ID</span>
                            <input value={clockTicketId} onChange={(event) => setClockTicketId(event.target.value)} placeholder="Optional ticket id" style={t.input} />
                        </label>
                        <label style={t.label}>
                            <span>Work note</span>
                            <input value={clockDescription} onChange={(event) => setClockDescription(event.target.value)} placeholder="Bench diagnostics, battery swap, etc." style={t.input} />
                        </label>
                    </div>
                    <div style={{ ...t.formActionsRow, marginTop: '14px' }}>
                        <button type="button" style={t.primaryBtn} disabled={Boolean(activeSession) || saving !== null} onClick={handleClockIn}>
                            {saving === 'clock-in' ? 'Clocking In...' : 'Clock In'}
                        </button>
                        <button type="button" style={t.secondaryBtn} disabled={!activeSession || saving !== null} onClick={handleClockOut}>
                            {saving === 'clock-out' ? 'Clocking Out...' : 'Clock Out'}
                        </button>
                    </div>
                </section>

                <section
                    style={{
                        ...t.panel,
                        padding: '18px',
                        background: 'linear-gradient(145deg, rgba(255,255,255,0.95) 0%, rgba(248,239,224,0.93) 100%)',
                        borderTop: '5px solid #d6842f',
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'baseline', flexWrap: 'wrap' }}>
                        <h3 style={{ margin: 0 }}>Summary Board</h3>
                        <span style={{ color: '#6d5437', fontSize: '0.86rem' }}>Latest entry: {latestEntryDate}</span>
                    </div>
                    <div style={{ marginTop: '12px', display: 'grid', gap: '9px' }}>
                        {technicianBreakdown.length > 0 ? (
                            technicianBreakdown.map(([name, loggedHours]) => (
                                <div
                                    key={name}
                                    style={{
                                        borderRadius: '12px',
                                        padding: '10px 12px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        gap: '10px',
                                        background: 'rgba(255,255,255,0.82)',
                                        border: '1px solid rgba(116,85,43,0.18)',
                                    }}
                                >
                                    <strong>{name}</strong>
                                    <span style={{ color: '#5f4729', fontWeight: 700 }}>{loggedHours}h</span>
                                </div>
                            ))
                        ) : (
                            <InlineState tone="info">No hours recorded in the current range.</InlineState>
                        )}
                    </div>
                </section>
            </div>

            <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'minmax(280px, 0.95fr) minmax(280px, 1.05fr)' }}>
                <section style={{ ...t.panel, padding: '18px' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '6px' }}>Filter History</h3>
                    <p style={{ ...t.meta, marginTop: 0, marginBottom: '10px' }}>Target specific dates and technicians for reporting.</p>
                    <form onSubmit={handleFilter} style={t.formStack}>
                        <div style={t.fieldGrid}>
                            <label style={t.label}>
                                <span>Start date</span>
                                <input type="date" value={filterStartDate} onChange={(event) => setFilterStartDate(event.target.value)} style={t.input} />
                            </label>
                            <label style={t.label}>
                                <span>End date</span>
                                <input type="date" value={filterEndDate} onChange={(event) => setFilterEndDate(event.target.value)} style={t.input} />
                            </label>
                            <label style={t.label}>
                                <span>Technician</span>
                                <input value={filterTechnician} onChange={(event) => setFilterTechnician(event.target.value)} style={t.input} list="filter-tech-roster" />
                                <datalist id="filter-tech-roster">
                                    {roster.map((name) => <option key={name} value={name} />)}
                                </datalist>
                            </label>
                        </div>
                        <div style={t.formActionsRow}>
                            <button type="submit" style={t.primaryBtn}>Apply Filters</button>
                            <button type="button" style={t.secondaryBtn} onClick={handleResetFilters}>Reset Filters</button>
                        </div>
                    </form>
                </section>

                <section style={{ ...t.panel, padding: '18px' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '6px' }}>Manual Adjustment</h3>
                    <p style={{ ...t.meta, marginTop: 0, marginBottom: '10px' }}>Backfill missed work blocks or correct completed sessions.</p>
                    <form onSubmit={handleAddHours} style={t.formStack}>
                        <div style={t.fieldGrid}>
                            <label style={t.label}>
                                <span>Work date</span>
                                <input type="date" value={manualWorkDate} onChange={(event) => setManualWorkDate(event.target.value)} style={t.input} />
                            </label>
                            <label style={t.label}>
                                <span>Hours worked</span>
                                <input type="number" step="0.25" min="0.25" value={manualHoursWorked} onChange={(event) => setManualHoursWorked(event.target.value)} style={t.input} />
                            </label>
                            <label style={t.label}>
                                <span>Ticket ID</span>
                                <input value={manualTicketId} onChange={(event) => setManualTicketId(event.target.value)} placeholder="Optional ticket id" style={t.input} />
                            </label>
                            <label style={t.label}>
                                <span>Work description</span>
                                <input value={manualWorkDescription} onChange={(event) => setManualWorkDescription(event.target.value)} placeholder="Replacement completed, troubleshooting, pickup prep..." style={t.input} />
                            </label>
                        </div>
                        <button type="submit" style={t.primaryBtn} disabled={saving !== null}>
                            {saving === 'manual' ? 'Saving...' : 'Log Manual Hours'}
                        </button>
                    </form>
                </section>
            </div>

            <SectionCard title="Hours Timeline" description="Newest records first, with quick context and direct ticket links." tone="soft">
                {loading ? (
                    <LoadingSpinner size="sm" message="Loading hours..." />
                ) : hours.length === 0 ? (
                    <InlineState tone="info">No hours logged yet.</InlineState>
                ) : (
                    <div style={{ display: 'grid', gap: '11px' }}>
                        {hours.map((log) => (
                            <article
                                key={log.id}
                                style={{
                                    borderRadius: '16px',
                                    border: '1px solid rgba(28,65,72,0.14)',
                                    background: 'linear-gradient(145deg, rgba(255,255,255,0.97) 0%, rgba(236,244,246,0.9) 100%)',
                                    boxShadow: '0 10px 20px rgba(15,42,47,0.07)',
                                    padding: '12px 14px',
                                    display: 'grid',
                                    gap: '8px',
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '9px', flexWrap: 'wrap' }}>
                                        <span style={{ borderRadius: '999px', background: '#113f49', color: '#eafcff', padding: '4px 10px', fontWeight: 700, fontSize: '0.82rem' }}>{formatDate(log.work_date)}</span>
                                        <strong>{log.technician}</strong>
                                    </div>
                                    <div style={{ fontWeight: 800, color: '#0f5865', fontSize: '1.05rem' }}>{log.hours_worked}h</div>
                                </div>
                                <div style={{ display: 'grid', gap: '5px', gridTemplateColumns: 'minmax(130px, 170px) 1fr', alignItems: 'start' }}>
                                    <div style={{ ...t.meta, marginTop: 0 }}>Ticket</div>
                                    <div style={{ ...t.copy, margin: 0 }}>
                                        {log.ticket_id ? (
                                            <Link to={`/tickets/${log.ticket_id}`} style={{ color: '#1b5a8a', fontWeight: 700, textDecoration: 'none' }}>
                                                #{log.ticket_id}
                                            </Link>
                                        ) : 'Unlinked'}
                                    </div>
                                    <div style={{ ...t.meta, marginTop: 0 }}>Description</div>
                                    <div style={{ ...t.copy, margin: 0 }}>{log.work_description || 'No work description provided.'}</div>
                                    <div style={{ ...t.meta, marginTop: 0 }}>Logged At</div>
                                    <div style={{ ...t.copy, margin: 0 }}>{formatDateTime(log.created_at)}</div>
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </SectionCard>
        </section>
    );
}
