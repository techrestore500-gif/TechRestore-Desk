import { QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";

import { AuthProvider } from "../auth/AuthProvider";
import { queryClient } from "../lib/queryClient";

export function AppProviders({ children }: { children: ReactNode }) {
    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
    );
}
