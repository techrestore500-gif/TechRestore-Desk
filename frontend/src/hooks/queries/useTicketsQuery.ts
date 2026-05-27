import { useQuery } from "@tanstack/react-query";

import { fetchTickets } from "../../api/tickets";
import { queryKeys } from "../queryKeys";

export function useTicketsQuery(search: string) {
    return useQuery({
        queryKey: queryKeys.tickets(search),
        queryFn: () => fetchTickets(search),
        staleTime: 15_000,
    });
}
