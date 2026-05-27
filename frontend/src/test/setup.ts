import { createElement } from 'react';
import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');

    const MemoryRouter: typeof actual.MemoryRouter = ((props: Parameters<typeof actual.MemoryRouter>[0]) => {
        const mergedFuture = {
            v7_startTransition: true,
            v7_relativeSplatPath: true,
            ...(props?.future ?? {}),
        };
        return createElement(actual.MemoryRouter, { ...props, future: mergedFuture }, props?.children);
    }) as typeof actual.MemoryRouter;

    return {
        ...actual,
        MemoryRouter,
    };
});
