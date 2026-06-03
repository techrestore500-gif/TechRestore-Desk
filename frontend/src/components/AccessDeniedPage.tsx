import { Link } from "react-router-dom";

import { SectionCard } from "./PageChrome";
import * as t from "../styles/theme";

export function AccessDeniedPage({
    title = "You do not have access",
    description = "Your account does not have permission to view this page.",
}: {
    title?: string;
    description?: string;
}) {
    return (
        <section style={t.pageWrap}>
            <SectionCard title={title} description={description} tone="soft">
                <div style={t.formActionsRow}>
                    <Link to="/" style={{ ...t.primaryBtn, textDecoration: "none" }}>
                        Back to dashboard
                    </Link>
                </div>
            </SectionCard>
        </section>
    );
}
