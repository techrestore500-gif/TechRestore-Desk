import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useUiStore } from "../store/uiStore";

export function useKeyboardShortcuts() {
    const navigate = useNavigate();
    const setCommandPaletteOpen = useUiStore((state) => state.setCommandPaletteOpen);

    useEffect(() => {
        const onKeyDown = (event: KeyboardEvent) => {
            const isCommandK = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
            if (isCommandK) {
                event.preventDefault();
                setCommandPaletteOpen(true);
                return;
            }

            if (event.key === "Escape") {
                setCommandPaletteOpen(false);
                return;
            }

            if (event.altKey) {
                if (event.key === "1") {
                    event.preventDefault();
                    navigate("/");
                    return;
                }
                if (event.key === "2") {
                    event.preventDefault();
                    navigate("/intake");
                    return;
                }
                if (event.key === "3") {
                    event.preventDefault();
                    navigate("/tickets");
                    return;
                }
                if (event.key === "4") {
                    event.preventDefault();
                    navigate("/queue");
                    return;
                }
                if (event.key === "5") {
                    event.preventDefault();
                    navigate("/inventory");
                }
            }
        };

        window.addEventListener("keydown", onKeyDown);
        return () => {
            window.removeEventListener("keydown", onKeyDown);
        };
    }, [navigate, setCommandPaletteOpen]);
}
