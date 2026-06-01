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
import { PageHeader } from '../components/PageChrome';
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

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Time Tracking"
                title="Hours"
                description="Track your time as Mattis with a live clock session, then review or correct past hours from the same screen."
            />

            {visibleError ? <div style={t.errorBanner}>{visibleError}</div> : null}

            <div style={t.detailGrid}>
                <div style={{ ...t.panel, background: 'linear-gradient(145deg, #ecfbf5 0%, #d8f2e6 100%)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap', alignItems: 'start' }}>
                        <div>
                            <h3 style={t.heading}>Clock Session</h3>
                            <p style={{ ...t.copy, marginTop: 0, marginBottom: '12px' }}>
                                Start a session when you begin work and clock out when you are done. The app will write the completed time into your hours log.
                            </p>
                        </div>
                        <div style={{ ...t.statusBadge, background: activeSession ? 'linear-gradient(145deg, #1f6657 0%, #184e42 100%)' : '#ffffff', color: activeSession ? '#f5efe3' : '#1d2b28', border: activeSession ? 'none' : '1px solid rgba(29, 43, 40, 0.18)', boxShadow: 'none' }}>
                            {activeSession ? 'Clocked In' : 'Clocked Out'}
                        </div>
                    </div>

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

                    <div style={{ display: 'grid', gap: '10px', marginTop: '18px' }}>
                        <div style={t.subCard}>
                            <strong>{activeSession ? `Started ${new Date(activeSession.clocked_in_at).toLocaleString()}` : 'No active session right now.'}</strong>
                            <div style={t.meta}>
                                {activeSession
                                    ? `${activeSession.elapsed_hours.toFixed(2)} hours so far${activeSession.ticket_id ? ` · Ticket #${activeSession.ticket_id}` : ''}`
                                    : 'Clock in to start tracking a repair block.'}
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                            <button type="button" style={t.primaryBtn} disabled={Boolean(activeSession) || saving !== null} onClick={handleClockIn}>
                                {saving === 'clock-in' ? 'Clocking In...' : 'Clock In'}
                            </button>
                            <button type="button" style={t.secondaryBtn} disabled={!activeSession || saving !== null} onClick={handleClockOut}>
                                {saving === 'clock-out' ? 'Clocking Out...' : 'Clock Out'}
                            </button>
                        </div>
                    </div>
                </div>

                <div style={{ display: 'grid', gap: '18px' }}>
                    <div style={{ ...t.panel, background: 'linear-gradient(145deg, #ecfbf5 0%, #d8f2e6 100%)' }}>
                        <h3 style={{ ...t.heading, color: '#1f6d4f' }}>Summary</h3>
                        <p style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0 0 10px', color: '#1f6d4f' }}>
                            Total: {summary?.total_hours ?? 0} hours
                        </p>
                        {summary && Object.keys(summary.by_technician).length > 0 ? (
                            <div style={{ display: 'grid', gap: '8px' }}>
                                {Object.entries(summary.by_technician).map(([name, loggedHours]) => (
                                    <div key={name} style={t.subCard}>
                                        <strong>{name}</strong>
                                        <div style={t.meta}>{loggedHours} hours in the selected range</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={t.copy}>No hours recorded in the current range.</p>
                        )}
                    </div>

                    <div style={t.panel}>
                        <h3 style={t.heading}>Filters</h3>
                        <form onSubmit={handleFilter} style={{ display: 'grid', gap: '16px' }}>
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
                            <button type="submit" style={t.primaryBtn}>Apply Filters</button>
                        </form>
                    </div>
                </div>
            </div>

            <div style={t.detailGrid}>
                <div style={t.panel}>
                    <h3 style={t.heading}>Manual Adjustment</h3>
                    <p style={{ ...t.copy, marginTop: 0, marginBottom: '12px' }}>
                        Use this when you need to backfill a missed entry or correct a finished block without using the live timer.
                    </p>
                    <form onSubmit={handleAddHours} style={{ display: 'grid', gap: '16px' }}>
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
                </div>

                <div style={t.panel}>
                    <h3 style={t.heading}>Hours Log</h3>
                    {loading ? (
                        <LoadingSpinner size="sm" message="Loading hours…" />
                    ) : hours.length === 0 ? (
                        <p style={t.copy}>No hours logged yet.</p>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={t.tableShell}>
                                <thead style={{ backgroundColor: '#1f4a41', color: '#f7f5ee' }}>
                                    <tr>
                                        <th style={t.tableHeaderCell}>Date</th>
                                        <th style={t.tableHeaderCell}>Technician</th>
                                        <th style={t.tableHeaderCell}>Hours</th>
                                        <th style={t.tableHeaderCell}>Ticket</th>
                                        <th style={t.tableHeaderCell}>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {hours.map((log, index) => (
                                        <tr key={log.id} style={{ borderBottom: '1px solid #ebf1ef', backgroundColor: index % 2 === 0 ? '#ffffff' : '#f8fbfa' }}>
                                            <td style={t.tableCell}>{new Date(log.work_date).toLocaleDateString()}</td>
                                            <td style={t.tableCell}>{log.technician}</td>
                                            <td style={{ ...t.tableCell, fontWeight: 700, color: '#1f5e4f' }}>{log.hours_worked}</td>
                                            <td style={t.tableCell}>
                                                {log.ticket_id ? (
                                                    <Link to={`/tickets/${log.ticket_id}`} style={{ color: '#1b5a8a', fontWeight: 600, textDecoration: 'none' }}>
                                                        #{log.ticket_id}
                                                    </Link>
                                                ) : '-'}
                                            </td>
                                            <td style={{ ...t.tableCell, color: '#576963' }}>{log.work_description || '-'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
