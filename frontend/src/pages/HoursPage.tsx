import { useEffect, useState } from 'react';

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
import { InlineState, PageHeader } from '../components/PageChrome';
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

function parseIsoDate(value: string): Date {
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, (month || 1) - 1, day || 1);
}

function toIsoDate(value: Date): string {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, '0');
    const day = String(value.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function toMonthLabel(value: Date): string {
    return value.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}

function InlineCalendar({
    title,
    selectedDate,
    onSelectDate,
}: {
    title: string;
    selectedDate: string;
    onSelectDate: (next: string) => void;
}) {
    const [visibleMonth, setVisibleMonth] = useState<Date>(() => {
        if (selectedDate) {
            const selected = parseIsoDate(selectedDate);
            return new Date(selected.getFullYear(), selected.getMonth(), 1);
        }
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), 1);
    });

    useEffect(() => {
        if (!selectedDate) return;
        const selected = parseIsoDate(selectedDate);
        setVisibleMonth(new Date(selected.getFullYear(), selected.getMonth(), 1));
    }, [selectedDate]);

    const year = visibleMonth.getFullYear();
    const month = visibleMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const leading = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const cells: Array<number | null> = [];
    for (let i = 0; i < leading; i += 1) {
        cells.push(null);
    }
    for (let day = 1; day <= daysInMonth; day += 1) {
        cells.push(day);
    }
    while (cells.length % 7 !== 0) {
        cells.push(null);
    }

    return (
        <div style={{ border: '1px solid #d9e2eb', borderRadius: '12px', padding: '10px', background: '#ffffff' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '8px' }}>
                <strong style={{ color: '#1a3443' }}>{title}</strong>
                <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                        type="button"
                        onClick={() => setVisibleMonth(new Date(year, month - 1, 1))}
                        style={{ ...t.secondaryBtn, padding: '4px 8px' }}
                        aria-label={`Previous month for ${title}`}
                    >
                        Prev
                    </button>
                    <button
                        type="button"
                        onClick={() => setVisibleMonth(new Date(year, month + 1, 1))}
                        style={{ ...t.secondaryBtn, padding: '4px 8px' }}
                        aria-label={`Next month for ${title}`}
                    >
                        Next
                    </button>
                </div>
            </div>

            <div style={{ fontSize: '0.85rem', color: '#496270', marginBottom: '8px' }}>{toMonthLabel(visibleMonth)}</div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', gap: '4px', marginBottom: '6px' }}>
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                    <div key={day} style={{ fontSize: '0.72rem', textAlign: 'center', color: '#60747f' }}>{day}</div>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', gap: '4px' }}>
                {cells.map((day, index) => {
                    if (day === null) {
                        return <div key={`empty-${index}`} style={{ height: '30px' }} />;
                    }
                    const iso = toIsoDate(new Date(year, month, day));
                    const selected = iso === selectedDate;
                    return (
                        <button
                            key={iso}
                            type="button"
                            onClick={() => onSelectDate(iso)}
                            style={{
                                height: '30px',
                                borderRadius: '8px',
                                border: selected ? '1px solid #0b5f6f' : '1px solid #d8e2ea',
                                background: selected ? '#0e6a78' : '#f9fbfc',
                                color: selected ? '#f3fbff' : '#244255',
                                cursor: 'pointer',
                                fontWeight: selected ? 700 : 500,
                            }}
                        >
                            {day}
                        </button>
                    );
                })}
            </div>

            <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                <div style={{ fontSize: '0.78rem', color: '#5b6f7b' }}>{selectedDate ? `Selected: ${selectedDate}` : 'No date selected'}</div>
                <button type="button" onClick={() => onSelectDate('')} style={{ ...t.secondaryBtn, padding: '4px 8px' }}>
                    Clear
                </button>
            </div>
        </div>
    );
}

export function HoursPage() {
    const [roster] = useState<string[]>(() => loadRoster());
    const defaultTechnician = roster[0] ?? DEFAULT_TECHNICIAN;
    const [refreshKey, setRefreshKey] = useState(0);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [saving, setSaving] = useState<'clock-in' | 'clock-out' | 'manual' | null>(null);

    const [technician, setTechnician] = useState(defaultTechnician);
    const [clockDescription, setClockDescription] = useState('');
    const [manualWorkDate, setManualWorkDate] = useState(todayIsoDate());
    const [manualHoursWorked, setManualHoursWorked] = useState('1');
    const [manualWorkDescription, setManualWorkDescription] = useState('');

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
        [technician, refreshKey],
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
                ticket_id: undefined,
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
                ticket_id: undefined,
                work_description: clockDescription || undefined,
            });
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
            });
            setManualHoursWorked('1');
            setManualWorkDescription('');
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
    const appliedRangeLabel = appliedStartDate || appliedEndDate
        ? `${appliedStartDate || 'Start'} to ${appliedEndDate || 'Now'}`
        : 'All time';

    const layout = {
        board: {
            display: 'grid',
            gap: '18px',
            background: '#f3f6f9',
            border: '1px solid #d6dee6',
            borderRadius: '20px',
            padding: '18px',
        },
        statRow: {
            display: 'grid',
            gap: '12px',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
        },
        statCard: {
            borderRadius: '14px',
            background: '#ffffff',
            border: '1px solid #d9e2eb',
            padding: '12px 13px',
            display: 'grid',
            gap: '4px',
        },
        statLabel: {
            fontSize: '0.72rem',
            letterSpacing: '0.08em',
            textTransform: 'uppercase' as const,
            color: '#566676',
            fontWeight: 700,
        },
        statValue: {
            fontSize: '1.38rem',
            lineHeight: 1.05,
            fontWeight: 800,
            color: '#102534',
        },
        split: {
            display: 'grid',
            gap: '14px',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        },
        panel: {
            background: '#ffffff',
            border: '1px solid #d9e2eb',
            borderRadius: '16px',
            padding: '14px',
            display: 'grid',
            gap: '12px',
            boxShadow: '0 1px 0 rgba(16, 37, 52, 0.03)',
        },
        panelTitleRow: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            gap: '10px',
            flexWrap: 'wrap' as const,
        },
        panelTitle: {
            margin: 0,
            color: '#0f2b3a',
            fontSize: '1.05rem',
        },
        tiny: {
            color: '#5a6d7b',
            fontSize: '0.82rem',
        },
        historyList: {
            display: 'grid',
            gap: '8px',
        },
        historyItem: {
            borderRadius: '12px',
            background: '#ffffff',
            border: '1px solid #d8e0e8',
            padding: '10px 11px',
            display: 'grid',
            gap: '6px',
        },
        historyTop: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '10px',
            flexWrap: 'wrap' as const,
        },
        badge: {
            display: 'inline-flex',
            alignItems: 'center',
            borderRadius: '999px',
            background: '#e8eff5',
            border: '1px solid #d0dbe6',
            color: '#244255',
            padding: '3px 9px',
            fontSize: '0.78rem',
            fontWeight: 700,
        },
    };

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Time Tracking"
                title="Hours"
                description="A clean workspace for timing sessions, corrections, and daily hour review."
            />

            {visibleError ? <InlineState tone="error">{visibleError}</InlineState> : null}

            <section style={layout.board}>
                <div style={layout.statRow}>
                    <div style={layout.statCard}>
                        <div style={layout.statLabel}>Total</div>
                        <div style={layout.statValue}>{totalHours}h</div>
                        <div style={layout.tiny}>Total: {totalHours} hours</div>
                    </div>
                    <div style={layout.statCard}>
                        <div style={layout.statLabel}>Session</div>
                        <div style={layout.statValue}>{activeSession ? 'Clocked In' : 'Clocked Out'}</div>
                        <div style={layout.tiny}>Elapsed {activeSessionElapsed}</div>
                    </div>
                    <div style={layout.statCard}>
                        <div style={layout.statLabel}>Range</div>
                        <div style={layout.statValue}>{appliedRangeLabel}</div>
                        <div style={layout.tiny}>{logCountLabel} · {activeTechnicians} techs</div>
                    </div>
                    <div style={layout.statCard}>
                        <div style={layout.statLabel}>Latest</div>
                        <div style={layout.statValue}>{latestEntryDate}</div>
                        <div style={layout.tiny}>Most recent work date</div>
                    </div>
                </div>

                <div style={layout.split}>
                    <section style={layout.panel}>
                        <div style={layout.panelTitleRow}>
                            <h3 style={layout.panelTitle}>Clock Session</h3>
                            <span style={layout.tiny}>{activeSession ? `Started ${formatDateTime(activeSession.clocked_in_at)}` : 'No active session'}</span>
                        </div>
                        <p style={{ ...t.copy, margin: 0 }}>Track live work without linking anything to tickets.</p>
                        <div style={t.fieldGrid}>
                            <label style={t.label}>
                                <span>Technician</span>
                                <input value={technician} onChange={(event) => setTechnician(event.target.value)} style={t.input} list="tech-roster" />
                                <datalist id="tech-roster">
                                    {roster.map((name) => <option key={name} value={name} />)}
                                </datalist>
                            </label>
                            <label style={t.label}>
                                <span>Work note</span>
                                <input value={clockDescription} onChange={(event) => setClockDescription(event.target.value)} placeholder="What are you working on?" style={t.input} />
                            </label>
                        </div>
                        <div style={t.formActionsRow}>
                            <button type="button" style={t.primaryBtn} disabled={Boolean(activeSession) || saving !== null} onClick={handleClockIn}>
                                {saving === 'clock-in' ? 'Clocking In...' : 'Clock In'}
                            </button>
                            <button type="button" style={t.secondaryBtn} disabled={!activeSession || saving !== null} onClick={handleClockOut}>
                                {saving === 'clock-out' ? 'Clocking Out...' : 'Clock Out'}
                            </button>
                        </div>
                    </section>

                    <section style={layout.panel}>
                        <div style={layout.panelTitleRow}>
                            <h3 style={layout.panelTitle}>Filters</h3>
                            <span style={layout.tiny}>Update summary and history</span>
                        </div>
                        <form onSubmit={handleFilter} style={t.formStack}>
                            <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
                                <InlineCalendar title="Start Date" selectedDate={filterStartDate} onSelectDate={setFilterStartDate} />
                                <InlineCalendar title="End Date" selectedDate={filterEndDate} onSelectDate={setFilterEndDate} />
                            </div>
                            <div style={t.fieldGrid}>
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

                        <div style={{ display: 'grid', gap: '7px' }}>
                            <div style={layout.statLabel}>By Technician</div>
                            {technicianBreakdown.length > 0 ? (
                                technicianBreakdown.map(([name, loggedHours]) => (
                                    <div key={name} style={{ ...layout.statCard, padding: '9px 10px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                                            <strong style={{ color: '#113447' }}>{name}</strong>
                                            <span style={{ fontWeight: 700, color: '#113447' }}>{loggedHours}h</span>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <InlineState tone="info">No hours recorded in the current range.</InlineState>
                            )}
                        </div>
                    </section>
                </div>

                <section style={layout.panel}>
                    <div style={layout.panelTitleRow}>
                        <h3 style={layout.panelTitle}>Manual Adjustment</h3>
                        <span style={layout.tiny}>Add or correct a time entry</span>
                    </div>
                    <form onSubmit={handleAddHours} style={t.formStack}>
                        <InlineCalendar title="Work Date" selectedDate={manualWorkDate} onSelectDate={setManualWorkDate} />
                        <div style={t.fieldGrid}>
                            <label style={t.label}>
                                <span>Hours worked</span>
                                <input type="number" step="0.25" min="0.25" value={manualHoursWorked} onChange={(event) => setManualHoursWorked(event.target.value)} style={t.input} />
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

                <section style={layout.panel}>
                    <div style={layout.panelTitleRow}>
                        <h3 style={layout.panelTitle}>Hours History</h3>
                        <span style={layout.tiny}>Most recent first</span>
                    </div>
                    {loading ? (
                        <LoadingSpinner size="sm" message="Loading hours..." />
                    ) : hours.length === 0 ? (
                        <InlineState tone="info">No hours logged yet.</InlineState>
                    ) : (
                        <div style={layout.historyList}>
                            {hours.map((log) => (
                                <article key={log.id} style={layout.historyItem}>
                                    <div style={layout.historyTop}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                            <span style={layout.badge}>{formatDate(log.work_date)}</span>
                                            <strong style={{ color: '#123346' }}>{log.technician}</strong>
                                        </div>
                                        <strong style={{ color: '#123346' }}>{log.hours_worked}h</strong>
                                    </div>
                                    <div style={{ ...t.copy, margin: 0 }}>{log.work_description || 'No work description provided.'}</div>
                                    <div style={layout.tiny}>Logged {formatDateTime(log.created_at)}</div>
                                </article>
                            ))}
                        </div>
                    )}
                </section>
            </section>
        </section>
    );
}
