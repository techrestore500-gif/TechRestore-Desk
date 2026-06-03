import type { ReactNode } from "react";

import type { AuthRole } from "../api/auth";
import { useAuth } from "../auth/AuthProvider";
import { hasRole } from "../auth/roles";
import { AccessDeniedPage } from "./AccessDeniedPage";

export function RequireRole({
    allowedRoles,
    children,
    deniedTitle,
    deniedDescription,
}: {
    allowedRoles: AuthRole[];
    children: ReactNode;
    deniedTitle?: string;
    deniedDescription?: string;
}) {
    const { user } = useAuth();
    if (!hasRole(user, allowedRoles)) {
        return <AccessDeniedPage title={deniedTitle} description={deniedDescription} />;
    }
    return <>{children}</>;
}
