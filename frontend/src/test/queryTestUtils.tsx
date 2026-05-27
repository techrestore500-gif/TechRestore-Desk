import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";

export function createTestQueryClient() {
    return new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
                gcTime: 0,
            },
            mutations: {
                retry: false,
            },
        },
    });
}

export function QueryTestProvider({ children }: { children: ReactNode }) {
    const client = createTestQueryClient();
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
