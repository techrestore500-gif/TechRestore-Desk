import { useQuery } from "@tanstack/react-query";

import { fetchTicketsPaged } from "../../api/tickets";
import { queryKeys } from "../queryKeys";

export function useTicketsPagedQuery(args: {
    page: number;
    pageSize: number;
    search: string;
    status?: string;
}) {
    return useQuery({
        queryKey: queryKeys.ticketsPaged({
            page: args.page,
            pageSize: args.pageSize,
            search: args.search,
            status: args.status,
        }),
        queryFn: () =>
            fetchTicketsPaged({
                page: args.page,
                pageSize: args.pageSize,
                search: args.search,
                status: args.status,
            }),
        staleTime: 10_000,
    });
}
