import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createPart, deletePart, updatePart, type Part } from "../../api/tickets";
import { queryKeys } from "../queryKeys";

type PartsSnapshot = Array<readonly [readonly unknown[], Part[] | undefined]>;

function collectPartCaches(queryClient: ReturnType<typeof useQueryClient>): PartsSnapshot {
    return queryClient.getQueriesData<Part[]>({ queryKey: ["parts"] });
}

function restorePartCaches(queryClient: ReturnType<typeof useQueryClient>, snapshot: PartsSnapshot) {
    for (const [key, value] of snapshot) {
        queryClient.setQueryData(key, value);
    }
}

export function useCreatePartMutation() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: createPart,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["parts"] });
        },
    });
}

export function useUpdatePartMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ partId, payload }: { partId: number; payload: Partial<Part> }) => updatePart(partId, payload),
        onMutate: async ({ partId, payload }) => {
            await queryClient.cancelQueries({ queryKey: ["parts"] });
            const snapshot = collectPartCaches(queryClient);

            for (const [key, value] of snapshot) {
                if (!value) {
                    continue;
                }
                queryClient.setQueryData<Part[]>(
                    key,
                    value.map((part) => (part.id === partId ? { ...part, ...payload } : part))
                );
            }

            return { snapshot };
        },
        onError: (_error, _vars, context) => {
            if (context?.snapshot) {
                restorePartCaches(queryClient, context.snapshot);
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["parts"] });
            queryClient.invalidateQueries({ queryKey: queryKeys.lowStock() });
        },
    });
}

export function useDeletePartMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deletePart,
        onMutate: async (partId) => {
            await queryClient.cancelQueries({ queryKey: ["parts"] });
            const snapshot = collectPartCaches(queryClient);

            for (const [key, value] of snapshot) {
                if (!value) {
                    continue;
                }
                queryClient.setQueryData<Part[]>(
                    key,
                    value.filter((part) => part.id !== partId)
                );
            }

            return { snapshot };
        },
        onError: (_error, _partId, context) => {
            if (context?.snapshot) {
                restorePartCaches(queryClient, context.snapshot);
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["parts"] });
            queryClient.invalidateQueries({ queryKey: queryKeys.lowStock() });
        },
    });
}
