import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { RequireRole } from "../components/RequireRole";
import AccessRequestsPage from "../pages/AccessRequestsPage";
import AccountPage from "../pages/AccountPage";
import DashboardPage from "../pages/DashboardPage";
import CustomerDetailPage from "../pages/CustomerDetailPage";
import IntakePrintPage from "../pages/IntakePrintPage";
import IntakePage from "../pages/IntakePage";
import InvoicePrintPage from "../pages/InvoicePrintPage";
import { InventoryPage } from "../pages/InventoryPage";
import LoginStatePage from "../pages/LoginStatePage";
import LoanerAgreementPrintPage from "../pages/LoanerAgreementPrintPage";
import InviteAcceptPage from "../pages/InviteAcceptPage";
import OperationsPage from "../pages/OperationsPage";
import PricingPage from "../pages/PricingPage";
import ReportsPage from "../pages/ReportsPage";
import SettingsPage from "../pages/SettingsPage";
import TicketDetailPage from "../pages/TicketDetailPage";
import TicketsPage from "../pages/TicketsPage";
import VoicemailPage from "../pages/VoicemailPage";
import MarketUpdatesAdminPage from "../pages/MarketUpdatesAdminPage";

const MARKET_HOSTNAME = "market.techrestoredesk.com";

function isStrictMarketHost(): boolean {
    return window.location.hostname.toLowerCase() === MARKET_HOSTNAME;
}

function canAccessMarketAdminOnThisHost(): boolean {
    const host = window.location.hostname.toLowerCase();
    return host === MARKET_HOSTNAME || host === "localhost" || host === "127.0.0.1" || host.endsWith(".onrender.com");
}

function MarketAdminHostRedirect() {
    window.location.replace(`https://${MARKET_HOSTNAME}/market-updates-admin`);
    return null;
}

function MarketAdminRouteElement() {
    if (!canAccessMarketAdminOnThisHost()) {
        return <MarketAdminHostRedirect />;
    }

    return (
        <RequireRole
            allowedRoles={["owner", "admin"]}
            deniedTitle="Market Updates Admin access is restricted"
            deniedDescription="Only owner/admin roles can manage market SMS controls."
        >
            <MarketUpdatesAdminPage />
        </RequireRole>
    );
}

export const router = createBrowserRouter([
    {
        path: "/login",
        element: <LoginStatePage />,
    },
    {
        path: "/invite/:token",
        element: <InviteAcceptPage />,
    },
    {
        path: "/",
        element: <AppShell />,
        children: [
            {
                index: true,
                element: isStrictMarketHost() ? <MarketAdminRouteElement /> : <DashboardPage />,
            },
            {
                path: "intake",
                element: <IntakePage />,
            },
            {
                path: "tickets",
                element: <TicketsPage />,
            },
            {
                path: "tickets/:ticketId",
                element: <TicketDetailPage />,
            },
            {
                path: "customers/:customerId",
                element: <CustomerDetailPage />,
            },
            {
                path: "tickets/:ticketId/invoice",
                element: <InvoicePrintPage />,
            },
            {
                path: "tickets/:ticketId/intake-print",
                element: <IntakePrintPage />,
            },
            {
                path: "tickets/:ticketId/loaner-agreement",
                element: <LoanerAgreementPrintPage />,
            },
            {
                path: "queue",
                element: <Navigate to="/tickets" replace />,
            },
            {
                path: "operations",
                element: <OperationsPage />,
            },
            {
                path: "reports",
                element: <ReportsPage />,
            },
            {
                path: "inventory",
                element: <InventoryPage />,
            },
            {
                path: "pricing",
                element: (
                    <RequireRole
                        allowedRoles={["owner", "admin", "front_desk", "technician", "viewer"]}
                        deniedTitle="Pricing access is restricted"
                        deniedDescription="You do not have permission to view pricing."
                    >
                        <PricingPage />
                    </RequireRole>
                ),
            },
            {
                path: "settings",
                element: (
                    <RequireRole
                        allowedRoles={["owner", "admin"]}
                        deniedTitle="Settings access is restricted"
                        deniedDescription="Only owner/admin roles can open settings."
                    >
                        <SettingsPage />
                    </RequireRole>
                ),
            },
            {
                path: "account",
                element: <AccountPage />,
            },
            {
                path: "users-invites",
                element: (
                    <RequireRole
                        allowedRoles={["owner"]}
                        deniedTitle="Team access is owner-only"
                        deniedDescription="Only the owner can manage invites and roles."
                    >
                        <AccessRequestsPage />
                    </RequireRole>
                ),
            },
            {
                path: "voicemail",
                element: <VoicemailPage />,
            },
            {
                path: "market-updates-admin",
                element: <MarketAdminRouteElement />,
            },
        ],
    },
]);