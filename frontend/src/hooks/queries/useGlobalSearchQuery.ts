import { useQuery } from "@tanstack/react-query";

import { fetchParts } from "../../api/inventory";
import { fetchTickets } from "../../api/tickets";

type GlobalSearchItem = {
    id: number;
    type: "ticket" | "part";
    label: string;
    subtitle: string;
    path: string;
};

async function runGlobalSearch(query: string): Promise<GlobalSearchItem[]> {
    const q = query.trim();
    if (q.length < 2) {
        return [];
    }

    const [tickets, parts] = await Promise.all([
        fetchTickets(q),
        fetchParts(),
    ]);

    const needle = q.toLowerCase();

    const partResults = parts
        .filter((part) => `${part.part_number} ${part.part_name} ${part.category}`.toLowerCase().includes(needle))
        .slice(0, 10)
        .map((part) => ({
            id: part.id,
            type: "part" as const,
            label: `${part.part_number} - ${part.part_name}`,
            subtitle: `${part.category} · Qty ${part.quantity_on_hand}`,
            path: `/inventory`,
        }));

    const ticketResults = tickets.slice(0, 10).map((ticket) => ({
        id: ticket.id,
        type: "ticket" as const,
        label: ticket.ticket_number,
        subtitle: `${ticket.customer_name} · ${ticket.status}`,
        path: `/tickets/${ticket.id}`,
    }));

    return [...ticketResults, ...partResults].slice(0, 24);
}

export function useGlobalSearchQuery(query: string, enabled: boolean) {
    return useQuery({
        queryKey: ["global-search", query],
        queryFn: () => runGlobalSearch(query),
        enabled: enabled && query.trim().length >= 2,
        staleTime: 20_000,
    });
}
