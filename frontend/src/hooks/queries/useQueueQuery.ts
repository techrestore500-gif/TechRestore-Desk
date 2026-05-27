import { useQuery } from "@tanstack/react-query";

import { fetchTechnicianQueue } from "../../api/tickets";
import { queryKeys } from "../queryKeys";

export function useQueueQuery() {
    return useQuery({
        queryKey: queryKeys.queue(),
        queryFn: fetchTechnicianQueue,
        staleTime: 10_000,
    });
}
