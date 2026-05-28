import { RouterProvider } from "react-router-dom";

import { AuthGate } from "./auth/AuthGate";
import { router } from "./routes/router";

export default function App() {
    return (
        <AuthGate>
            <RouterProvider router={router} />
        </AuthGate>
    );
}