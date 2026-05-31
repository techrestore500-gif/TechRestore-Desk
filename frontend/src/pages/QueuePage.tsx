import { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { TechnicianQueue, QueueTicket, assignQueueTicket } from '../api/tickets';
import { LoadingBoundary } from '../components/LoadingBoundary';
import { PageHeader } from '../components/PageChrome';
import { ScannerInput } from '../components/ScannerInput';
import { queryKeys } from '../hooks/queryKeys';
import { useQueueQuery } from '../hooks/queries/useQueueQuery';
import { useUiStore } from '../store/uiStore';
import * as t from '../styles/theme';

const statusColors: Record<string, { bg: string; border: string; text: string }> = {
    'Loaner Outstanding': { bg: '#fff1eb', border: '#f3c8b6', text: '#8f2f16' },
    'Waiting for Parts': { bg: '#fff7e6', border: '#f2dfad', text: '#7d5a00' },
    'Customer Approval Needed': { bg: '#fdf3ff', border: '#e6c8f3', text: '#6f2f82' },
    'New Intake': { bg: '#ecf8f5', border: '#bde4d9', text: '#185544' },
    'Needs Diagnosis': { bg: '#edf4fb', border: '#c5ddf2', text: '#224f7a' },
};

const sectionCardStyle = {
    border: '1px solid rgba(23, 54, 47, 0.12)',
    borderRadius: '14px',
    background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(243,249,247,0.88) 100%)',
    boxShadow: '0 10px 22px rgba(19, 47, 41, 0.08)',
    padding: '1rem',
};

export function QueuePage() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [viewName, setViewName] = useState('');
    const quickFilter = useUiStore((state) => state.queueQuickFilter);
    const setQuickFilter = useUiStore((state) => state.setQueueQuickFilter);
    const queueSavedViews = useUiStore((state) => state.queueSavedViews);
    const saveQueueView = useUiStore((state) => state.saveQueueView);
    const applyQueueView = useUiStore((state) => state.applyQueueView);
    const deleteQueueView = useUiStore((state) => state.deleteQueueView);
    const [assigningTicketId, setAssigningTicketId] = useState<number | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const { data: queue, isLoading, error } = useQueueQuery();

    const assignMutation = useMutation({
        mutationFn: ({ ticketId, technician }: { ticketId: number; technician: string | null }) =>
            assignQueueTicket(ticketId, technician),
        onMutate: async ({ ticketId, technician }) => {
            setAssigningTicketId(ticketId);
            setActionError(null);
            setActionMessage(`Saving assignment for ticket #${ticketId}...`);
            await queryClient.cancelQueries({ queryKey: queryKeys.queue() });
            const previous = queryClient.getQueryData<TechnicianQueue>(queryKeys.queue());

            if (previous) {
                const updated = Object.fromEntries(
                    Object.entries(previous).map(([status, tickets]) => [
                        status,
                        tickets.map((ticket) =>
                            ticket.id === ticketId ? { ...ticket, assigned_technician: technician } : ticket
                        ),
                    ])
                ) as TechnicianQueue;

                queryClient.setQueryData(queryKeys.queue(), updated);
            }

            return { previous };
        },
        onError: (_error, _vars, context) => {
            setActionMessage(null);
            setActionError("Could not update assignment. Please try again.");
            if (context?.previous) {
                queryClient.setQueryData(queryKeys.queue(), context.previous);
            }
        },
        onSettled: () => {
            setAssigningTicketId(null);
            setActionMessage("Assignment updated.");
            queryClient.invalidateQueries({ queryKey: queryKeys.queue() });
        },
    });

    const handleRefresh = () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.queue() });
    };

    const statusOrder = [
        'Loaner Outstanding',
        'Waiting for Parts',
        'Customer Approval Needed',
        'New Intake',
        'Needs Diagnosis',
    ];

    const filterTickets = (tickets: QueueTicket[]) => {
        const q = quickFilter.trim().toLowerCase();
        if (!q) {
            return tickets;
        }
        return tickets.filter((ticket) =>
            `${ticket.ticket_number} ${ticket.customer_name ?? ''} ${ticket.customer_phone ?? ''} ${ticket.issue_category} ${ticket.status}`
                .toLowerCase()
                .includes(q)
        );
    };

    const technicianOptions = useMemo(() => {
        if (!queue) {
            return [] as string[];
        }
        const set = new Set<string>();
        Object.values(queue).forEach((tickets) => {
            tickets.forEach((ticket) => {
                if (ticket.assigned_technician) {
                    set.add(ticket.assigned_technician);
                }
            });
        });
        return Array.from(set).sort();
    }, [queue]);

    const renderStatusSection = (status: string, sourceTickets: QueueTicket[]) => {
        const tickets = filterTickets(sourceTickets);
        const color = statusColors[status] ?? { bg: '#f2f4f3', border: '#d9dfdd', text: '#33453f' };
        return (
            <div key={status} style={{ marginBottom: '1.2rem', ...sectionCardStyle }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.8rem', marginBottom: '0.6rem' }}>
                    <h3 style={{ color: '#1f3c35', margin: 0, fontSize: '1.06rem' }}>{status}</h3>
                    <span style={{ background: color.bg, color: color.text, border: `1px solid ${color.border}`, borderRadius: '999px', padding: '0.2rem 0.65rem', fontWeight: 700, fontSize: '0.82rem' }}>
                        {tickets.length}
                    </span>
                </div>
                {tickets.length === 0 ? (
                    <p style={{ color: '#7f8c8d', fontStyle: 'italic', margin: '0.4rem 0 0.2rem' }}>No tickets in this status.</p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                        {tickets.map(ticket => (
                            <div
                                key={ticket.id}
                                role='button'
                                tabIndex={0}
                                style={{
                                    border: `1px solid ${color.border}`,
                                    borderRadius: '10px',
                                    padding: '0.62rem 0.72rem',
                                    backgroundColor: color.bg,
                                    cursor: 'pointer',
                                    transition: 'transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease',
                                    boxShadow: '0 2px 8px rgba(19, 47, 41, 0.05)',
                                }}
                                onMouseEnter={(e) => {
                                    const node = e.currentTarget as HTMLDivElement;
                                    node.style.transform = 'translateY(-2px)';
                                    node.style.boxShadow = '0 10px 16px rgba(19, 47, 41, 0.15)';
                                }}
                                onMouseLeave={(e) => {
                                    const node = e.currentTarget as HTMLDivElement;
                                    node.style.transform = 'translateY(0)';
                                    node.style.boxShadow = '0 4px 10px rgba(19, 47, 41, 0.05)';
                                }}
                                onClick={() => {
                                    navigate(`/tickets/${ticket.id}`);
                                }}
                                onKeyDown={(event) => {
                                    if (event.key === 'Enter' || event.key === ' ') {
                                        event.preventDefault();
                                        navigate(`/tickets/${ticket.id}`);
                                    }
                                }}
                            >
                                <div style={{ display: 'grid', gap: '6px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', alignItems: 'center' }}>
                                        <strong style={{ fontSize: '0.95rem', color: '#17312a' }}>
                                            {ticket.ticket_number} {ticket.manufacturer} {ticket.model_name}
                                        </strong>
                                        <span style={{ color: '#5d716d', fontSize: '0.8rem' }}>{new Date(ticket.intake_date).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
                                    </div>
                                    <div style={{ color: '#2c3e50', fontSize: '0.88rem' }}>
                                        {ticket.issue_category} · {ticket.customer_name || 'Unknown customer'}
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' as const }}>
                                        <label style={{ color: '#4f6560', fontSize: '0.8rem', fontWeight: 700 }}>Assigned</label>
                                        <select
                                            value={ticket.assigned_technician ?? ''}
                                            onChange={(event) => {
                                                assignMutation.mutate({
                                                    ticketId: ticket.id,
                                                    technician: event.target.value ? event.target.value : null,
                                                });
                                            }}
                                            disabled={assigningTicketId === ticket.id}
                                        >
                                            <option value="">Unassigned</option>
                                            {technicianOptions.map((name) => (
                                                <option key={name} value={name}>{name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div>
            <PageHeader
                kicker="Queue"
                title="Technician Queue"
                description="Compact work queue grouped by status for fast technician updates."
                actions={
                    <button
                        onClick={handleRefresh}
                        style={{
                            padding: '8px 16px',
                            background: 'linear-gradient(145deg, #1f6657 0%, #184e42 100%)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '999px',
                            cursor: 'pointer',
                            fontSize: '0.88rem',
                            fontWeight: 700,
                            boxShadow: '0 6px 12px rgba(23, 70, 60, 0.2)',
                            whiteSpace: 'nowrap' as const,
                        }}
                    >
                        ↺ Refresh
                    </button>
                }
            />

            <div style={{ display: 'grid', gap: '8px', marginBottom: '12px' }}>
                {actionError ? <div style={{ ...t.errorBanner, marginBottom: '4px' }}>{actionError}</div> : null}
                {actionMessage ? <div style={{ ...t.subCard, color: '#0f5132', borderColor: '#c7ead5', background: '#e9f9ef' }}>{actionMessage}</div> : null}
                <ScannerInput
                    value={quickFilter}
                    onChange={setQuickFilter}
                    onScanSubmit={setQuickFilter}
                    placeholder="Quick filter queue"
                />
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <input
                        value={viewName}
                        onChange={(event) => setViewName(event.target.value)}
                        placeholder='Queue view name'
                        style={{
                            minWidth: '170px',
                            padding: '8px 10px',
                            borderRadius: '10px',
                            border: '1px solid rgba(29, 43, 40, 0.18)',
                        }}
                    />
                    <button
                        type='button'
                        onClick={() => {
                            saveQueueView(viewName);
                            setViewName('');
                        }}
                        style={{
                            padding: '8px 12px',
                            borderRadius: '999px',
                            border: '1px solid rgba(29, 43, 40, 0.18)',
                            background: '#fff',
                            cursor: 'pointer',
                        }}
                    >
                        Save view
                    </button>
                    {Object.keys(queueSavedViews).map((name) => (
                        <div key={name} style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                            <button
                                type='button'
                                onClick={() => applyQueueView(name)}
                                style={{
                                    padding: '8px 12px',
                                    borderRadius: '999px',
                                    border: '1px solid rgba(29, 43, 40, 0.18)',
                                    background: '#fff',
                                    cursor: 'pointer',
                                }}
                            >
                                {name}
                            </button>
                            <button
                                type='button'
                                onClick={() => deleteQueueView(name)}
                                style={{
                                    padding: '8px 10px',
                                    borderRadius: '999px',
                                    border: '1px solid rgba(29, 43, 40, 0.18)',
                                    background: '#fff',
                                    cursor: 'pointer',
                                }}
                            >
                                x
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            <LoadingBoundary loading={isLoading} error={error instanceof Error ? error.message : null} loadingMessage="Loading queue...">
                {queue ? (
                    <div>
                        {statusOrder.map((status) => {
                            const tickets = queue[status as keyof TechnicianQueue] || [];
                            return renderStatusSection(status, tickets);
                        })}
                    </div>
                ) : (
                    <p style={{ color: '#7f8c8d' }}>No queue data available.</p>
                )}
            </LoadingBoundary>
        </div>
    );
}
