import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export type TablePagination = {
    page: number;
    pageSize: number;
};

type UiState = {
    ticketSearch: string;
    ticketStatusFilter: string;
    queueQuickFilter: string;
    inventoryFilters: {
        category: string;
        status: string;
        lowStockOnly: boolean;
    };
    inventoryPagination: TablePagination;
    commandPaletteOpen: boolean;
    commandPaletteQuery: string;
    scannerMode: boolean;
    ticketSavedViews: Record<string, { search: string; status: string }>;
    queueSavedViews: Record<string, { quickFilter: string }>;
    setTicketSearch: (value: string) => void;
    setTicketStatusFilter: (value: string) => void;
    setQueueQuickFilter: (value: string) => void;
    setInventoryFilters: (next: Partial<UiState["inventoryFilters"]>) => void;
    setInventoryPagination: (next: Partial<TablePagination>) => void;
    setCommandPaletteOpen: (isOpen: boolean) => void;
    setCommandPaletteQuery: (value: string) => void;
    toggleScannerMode: () => void;
    saveTicketView: (name: string) => void;
    applyTicketView: (name: string) => void;
    deleteTicketView: (name: string) => void;
    saveQueueView: (name: string) => void;
    applyQueueView: (name: string) => void;
    deleteQueueView: (name: string) => void;
};

export const useUiStore = create<UiState>()(
    persist(
        (set, get) => ({
            ticketSearch: "",
            ticketStatusFilter: "",
            queueQuickFilter: "",
            inventoryFilters: {
                category: "",
                status: "",
                lowStockOnly: false,
            },
            inventoryPagination: {
                page: 1,
                pageSize: 15,
            },
            commandPaletteOpen: false,
            commandPaletteQuery: "",
            scannerMode: false,
            ticketSavedViews: {},
            queueSavedViews: {},
            setTicketSearch: (value) => set({ ticketSearch: value }),
            setTicketStatusFilter: (value) => set({ ticketStatusFilter: value }),
            setQueueQuickFilter: (value) => set({ queueQuickFilter: value }),
            setInventoryFilters: (next) =>
                set((state) => ({
                    inventoryFilters: {
                        ...state.inventoryFilters,
                        ...next,
                    },
                })),
            setInventoryPagination: (next) =>
                set((state) => ({
                    inventoryPagination: {
                        ...state.inventoryPagination,
                        ...next,
                    },
                })),
            setCommandPaletteOpen: (isOpen) => set({ commandPaletteOpen: isOpen }),
            setCommandPaletteQuery: (value) => set({ commandPaletteQuery: value }),
            toggleScannerMode: () => set((state) => ({ scannerMode: !state.scannerMode })),
            saveTicketView: (name) => {
                const viewName = name.trim();
                if (!viewName) {
                    return;
                }
                const state = get();
                set({
                    ticketSavedViews: {
                        ...state.ticketSavedViews,
                        [viewName]: {
                            search: state.ticketSearch,
                            status: state.ticketStatusFilter,
                        },
                    },
                });
            },
            applyTicketView: (name) => {
                const view = get().ticketSavedViews[name];
                if (!view) {
                    return;
                }
                set({
                    ticketSearch: view.search,
                    ticketStatusFilter: view.status,
                });
            },
            deleteTicketView: (name) => {
                const state = get();
                const next = { ...state.ticketSavedViews };
                delete next[name];
                set({ ticketSavedViews: next });
            },
            saveQueueView: (name) => {
                const viewName = name.trim();
                if (!viewName) {
                    return;
                }
                const state = get();
                set({
                    queueSavedViews: {
                        ...state.queueSavedViews,
                        [viewName]: {
                            quickFilter: state.queueQuickFilter,
                        },
                    },
                });
            },
            applyQueueView: (name) => {
                const view = get().queueSavedViews[name];
                if (!view) {
                    return;
                }
                set({ queueQuickFilter: view.quickFilter });
            },
            deleteQueueView: (name) => {
                const state = get();
                const next = { ...state.queueSavedViews };
                delete next[name];
                set({ queueSavedViews: next });
            },
        }),
        {
            name: "tech-restore-ui-store",
            storage: createJSONStorage(() => {
                if (
                    typeof window !== "undefined" &&
                    window.localStorage &&
                    typeof window.localStorage.getItem === "function" &&
                    typeof window.localStorage.setItem === "function" &&
                    typeof window.localStorage.removeItem === "function"
                ) {
                    return window.localStorage;
                }
                return {
                    getItem: () => null,
                    setItem: () => undefined,
                    removeItem: () => undefined,
                };
            }),
            partialize: (state) => ({
                ticketSearch: state.ticketSearch,
                ticketStatusFilter: state.ticketStatusFilter,
                queueQuickFilter: state.queueQuickFilter,
                inventoryFilters: state.inventoryFilters,
                inventoryPagination: state.inventoryPagination,
                scannerMode: state.scannerMode,
                ticketSavedViews: state.ticketSavedViews,
                queueSavedViews: state.queueSavedViews,
            }),
        }
    )
);
