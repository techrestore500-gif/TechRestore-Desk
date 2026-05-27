import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import DashboardPage from "../pages/DashboardPage";
import { DonorsPage } from "../pages/DonorsPage";
import { HoursPage } from "../pages/HoursPage";
import CustomerDetailPage from "../pages/CustomerDetailPage";
import IntakePrintPage from "../pages/IntakePrintPage";
import IntakePage from "../pages/IntakePage";
import InvoicePrintPage from "../pages/InvoicePrintPage";
import { InventoryPage } from "../pages/InventoryPage";
import LoanerAgreementPrintPage from "../pages/LoanerAgreementPrintPage";
import LoanersPage from "../pages/LoanersPage";
import { QueuePage } from "../pages/QueuePage";
import ReportsPage from "../pages/ReportsPage";
import SettingsPage from "../pages/SettingsPage";
import TicketDetailPage from "../pages/TicketDetailPage";
import TicketsPage from "../pages/TicketsPage";
import VoicemailPage from "../pages/VoicemailPage";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <AppShell />,
        children: [
            {
                index: true,
                element: <DashboardPage />,
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
                element: <QueuePage />,
            },
            {
                path: "hours",
                element: <HoursPage />,
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
                path: "donors",
                element: <DonorsPage />,
            },
            {
                path: "loaners",
                element: <LoanersPage />,
            },
            {
                path: "settings",
                element: <SettingsPage />,
            },
            {
                path: "voicemail",
                element: <VoicemailPage />,
            },
        ],
    },
]);