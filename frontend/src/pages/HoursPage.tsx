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

function formatDate(value: string) {
    return new Date(value).toLocaleDateString();
}

function formatDateTime(value: string) {
    return new Date(value).toLocaleString();
}

function monthLabel(value: Date): string {
    return value.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}

function FullCalendar({ selectedDate, onSelectDate }: { selectedDate: string; onSelectDate: (iso: string) => void }) {
    const [visibleMonth, setVisibleMonth] = useState<Date>(() => {
        const selected = parseIsoDate(selectedDate);
        return new Date(selected.getFullYear(), selected.getMonth(), 1);
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
        <section style={{ ...t.panel, background: '#ffffff', border: '1px solid #dce5ed', borderRadius: '12px', boxShadow: 'none', padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
                <h3 style={{ margin: 0, color: '#1a2c39', fontSize: '1rem' }}>Calendar</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <button type="button" style={{ ...t.secondaryBtn, padding: '6px 10px' }} onClick={() => setVisibleMonth(new Date(year, month - 1, 1))}>
                        Prev
                    </button>
                    <strong style={{ color: '#203645', minWidth: '150px', textAlign: 'center' }}>{monthLabel(visibleMonth)}</strong>
                    <button type="button" style={{ ...t.secondaryBtn, padding: '6px 10px' }} onClick={() => setVisibleMonth(new Date(year, month + 1, 1))}>
                        Next
                    </button>
                </div>
            </div>

            <div style={{ marginTop: '10px', display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', gap: '6px' }}>
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((name) => (
                    <div key={name} style={{ textAlign: 'center', fontSize: '0.75rem', color: '#607384', fontWeight: 600 }}>{name}</div>
                ))}

                {cells.map((day, index) => {
                    if (day === null) {
                        return <div key={`empty-${index}`} style={{ height: '42px' }} />;
                    }
                    const iso = toIsoDate(new Date(year, month, day));
                    const selected = iso === selectedDate;
                    return (
                        <button
                            key={iso}
                            type="button"
                            onClick={() => onSelectDate(iso)}
                            style={{
                                height: '42px',
                                borderRadius: '9px',
                                border: selected ? '1px solid #0b5d6a' : '1px solid #d7e2ea',
                                background: selected ? '#0f6a77' : '#f8fbfd',
                                color: selected ? '#f4fcff' : '#2e4757',
                                cursor: 'pointer',
                                fontWeight: selected ? 700 : 500,
                                fontSize: '0.9rem',
                            }}
                        >
                            {day}
                        </button>
                    );
                })}
            </div>

            <div style={{ marginTop: '10px', color: '#5c7180', fontSize: '0.84rem' }}>
                Selected date: <strong style={{ color: '#1f3543' }}>{selectedDate}</strong>
            </div>
        </section>
    );
}

export function HoursPage() {
    const [roster] = useState<string[]>(() => loadRoster());
    const defaultTechnician = roster[0] ?? DEFAULT_TECHNICIAN;
    const [refreshKey, setRefreshKey] = useState(0);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [saving, setSaving] = useState<'clock-in' | 'clock-out' | 'manual' | null>(null);

    const [technician, setTechnician] = useState(defaultTechnician);
    const [manualWorkDate, setManualWorkDate] = useState(todayIsoDate());
    const [manualHoursWorked, setManualHoursWorked] = useState('1');
    const [selectedDate, setSelectedDate] = useState(todayIsoDate());

    useEffect(() => {
        if (!roster.includes(technician)) {
            setTechnician(defaultTechnician);
        }
    }, [defaultTechnician, roster, technician]);

    const { data, loading, error } = useAsyncData(async () => {
        const [hoursData, summaryData] = await Promise.all([
            fetchHours(selectedDate, selectedDate, undefined),
            fetchHoursSummary(selectedDate, selectedDate, undefined),
        ]);
        return {
            hours: hoursData,
            summary: summaryData,
        };
    }, [selectedDate, refreshKey]);

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
                work_description: undefined,
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
                work_description: undefined,
            });
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
            });
            setManualHoursWorked('1');
            refreshData();
        } catch (err) {
            setSubmitError(err instanceof Error ? err.message : 'Failed to log hours');
        } finally {
            setSaving(null);
        }
    }

    const totalHours = summary?.total_hours ?? 0;
    const activeSessionElapsed = activeSession ? `${activeSession.elapsed_hours.toFixed(2)}h` : '0.00h';
    const isClockedIn = Boolean(activeSession);

    const clockInButtonStyle = {
        ...t.primaryBtn,
        padding: '10px 14px',
        transition: 'all 180ms ease',
        transform: isClockedIn ? 'scale(0.98)' : 'scale(1)',
        opacity: isClockedIn ? 0.55 : 1,
        boxShadow: isClockedIn
            ? 'inset 0 0 0 1px rgba(18, 54, 58, 0.18)'
            : '0 11px 24px rgba(17, 83, 86, 0.26)',
    } as const;

    const clockOutButtonStyle = {
        ...t.secondaryBtn,
        padding: '10px 14px',
        transition: 'all 180ms ease',
        transform: isClockedIn ? 'scale(1)' : 'scale(0.98)',
        opacity: isClockedIn ? 1 : 0.65,
        border: isClockedIn ? '1px solid rgba(19, 78, 61, 0.44)' : '1px solid rgba(26, 51, 58, 0.2)',
        background: isClockedIn ? 'linear-gradient(145deg, #e8fff5 0%, #d5f5e6 100%)' : 'rgba(255,255,255,0.78)',
        color: isClockedIn ? '#0f4f41' : '#163740',
        boxShadow: isClockedIn ? '0 8px 16px rgba(19, 78, 61, 0.16)' : 'none',
    } as const;

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Time Tracking"
                title="Hours"
                description="Clock in/out, then pick a day on the calendar to view and log hours."
            />

            {visibleError ? <InlineState tone="error">{visibleError}</InlineState> : null}

            <section style={{ ...t.panel, background: '#f8fbfd', border: '1px solid #d8e3eb', borderRadius: '14px', boxShadow: 'none', padding: '14px', display: 'grid', gap: '12px' }}>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
                    <label style={t.label}>
                        <span>Technician</span>
                        <input value={technician} onChange={(event) => setTechnician(event.target.value)} style={t.input} list="tech-roster" />
                        <datalist id="tech-roster">
                            {roster.map((name) => <option key={name} value={name} />)}
                        </datalist>
                    </label>
                    <div style={{ ...t.panel, padding: '10px 12px', boxShadow: 'none', border: '1px solid #dde6ee', background: '#fff' }}>
                        <div style={{ fontSize: '0.8rem', color: '#5c7080' }}>Session</div>
                        <div style={{ fontWeight: 700, color: '#203543' }}>{activeSession ? 'Clocked In' : 'Clocked Out'}</div>
                        <div style={{ fontSize: '0.82rem', color: '#5c7080' }}>Elapsed {activeSessionElapsed}</div>
                    </div>
                    <div style={{ ...t.panel, padding: '10px 12px', boxShadow: 'none', border: '1px solid #dde6ee', background: '#fff' }}>
                        <div style={{ fontSize: '0.8rem', color: '#5c7080' }}>Selected Day</div>
                        <div style={{ fontWeight: 700, color: '#203543' }}>{selectedDate}</div>
                        <div style={{ fontSize: '0.82rem', color: '#5c7080' }}>Total: {totalHours} hours</div>
                    </div>
                </div>

                <div style={t.formActionsRow}>
                    <button type="button" style={clockInButtonStyle} disabled={isClockedIn || saving !== null} onClick={handleClockIn}>
                        {saving === 'clock-in' ? 'Clocking In...' : 'Clock In'}
                    </button>
                    <button type="button" style={clockOutButtonStyle} disabled={!isClockedIn || saving !== null} onClick={handleClockOut}>
                        {saving === 'clock-out' ? 'Clocking Out...' : 'Clock Out'}
                    </button>
                </div>

                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        borderRadius: '10px',
                        border: isClockedIn ? '1px solid #9fddc0' : '1px solid #d6dee5',
                        background: isClockedIn ? '#ecfff4' : '#f5f8fb',
                        color: isClockedIn ? '#165948' : '#4e6473',
                        padding: '8px 10px',
                        fontSize: '0.86rem',
                        fontWeight: 700,
                        transition: 'all 180ms ease',
                    }}
                >
                    <span
                        style={{
                            width: '9px',
                            height: '9px',
                            borderRadius: '50%',
                            background: isClockedIn ? '#1f9d6f' : '#8ea0ad',
                            boxShadow: isClockedIn ? '0 0 0 3px rgba(31, 157, 111, 0.2)' : 'none',
                            transition: 'all 180ms ease',
                        }}
                    />
                    {isClockedIn ? 'Clocked In - active session is running.' : 'Clocked Out - no active session.'}
                </div>

                <FullCalendar
                    selectedDate={selectedDate}
                    onSelectDate={(iso) => {
                        setSelectedDate(iso);
                        setManualWorkDate(iso);
                    }}
                />
            </section>

            <section style={{ ...t.panel, background: '#ffffff', border: '1px solid #dce6ee', borderRadius: '12px', boxShadow: 'none' }}>
                <h3 style={{ marginTop: 0, marginBottom: '8px', color: '#1d3240' }}>Manual Log</h3>
                <form onSubmit={handleAddHours} style={{ display: 'grid', gap: '12px' }}>
                    <div style={t.fieldGrid}>
                        <label style={t.label}>
                            <span>Technician</span>
                            <input value={technician} onChange={(event) => setTechnician(event.target.value)} style={t.input} list="manual-tech-roster" />
                            <datalist id="manual-tech-roster">
                                {roster.map((name) => <option key={name} value={name} />)}
                            </datalist>
                        </label>
                        <label style={t.label}>
                            <span>Date</span>
                            <input value={manualWorkDate} readOnly style={{ ...t.input, background: '#f6f9fb', color: '#3f5666' }} />
                        </label>
                        <label style={t.label}>
                            <span>Hours worked</span>
                            <input type="number" step="0.25" min="0.25" value={manualHoursWorked} onChange={(event) => setManualHoursWorked(event.target.value)} style={t.input} />
                        </label>
                    </div>
                    <button type="submit" style={t.primaryBtn} disabled={saving !== null}>
                        {saving === 'manual' ? 'Saving...' : 'Log Manual Hours'}
                    </button>
                </form>
            </section>

            <section style={{ ...t.panel, background: '#ffffff', border: '1px solid #dce6ee', borderRadius: '12px', boxShadow: 'none' }}>
                <h3 style={{ marginTop: 0, marginBottom: '8px', color: '#1d3240' }}>Day History</h3>
                {loading ? (
                    <LoadingSpinner size="sm" message="Loading hours..." />
                ) : hours.length === 0 ? (
                    <InlineState tone="info">No hours logged for this day.</InlineState>
                ) : (
                    <div style={{ display: 'grid', gap: '8px' }}>
                        {hours.map((log) => (
                            <article key={log.id} style={{ borderRadius: '10px', border: '1px solid #dce6ee', background: '#f9fcfd', padding: '9px 10px', display: 'grid', gap: '5px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                                    <strong style={{ color: '#244356' }}>{log.technician}</strong>
                                    <strong style={{ color: '#244356' }}>{log.hours_worked}h</strong>
                                </div>
                                <div style={{ color: '#5d7280', fontSize: '0.82rem' }}>Work date: {formatDate(log.work_date)}</div>
                                <div style={{ color: '#5d7280', fontSize: '0.82rem' }}>Logged {formatDateTime(log.created_at)}</div>
                            </article>
                        ))}
                    </div>
                )}
            </section>
        </section>
    );
}
