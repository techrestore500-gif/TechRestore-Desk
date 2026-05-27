import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useAsyncData } from './useAsyncData';

function createDeferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (reason?: unknown) => void;
    const promise = new Promise<T>((promiseResolve, promiseReject) => {
        resolve = promiseResolve;
        reject = promiseReject;
    });

    return { promise, resolve, reject };
}

describe('useAsyncData', () => {
    it('tracks loading and resolved data', async () => {
        const deferred = createDeferred<number>();

        const { result } = renderHook(() => useAsyncData(() => deferred.promise, []));

        expect(result.current.loading).toBe(true);
        expect(result.current.data).toBeUndefined();
        expect(result.current.error).toBeNull();

        act(() => {
            deferred.resolve(42);
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.data).toBe(42);
        expect(result.current.error).toBeNull();
    });

    it('captures errors', async () => {
        const deferred = createDeferred<number>();
        const error = new Error('boom');

        const { result } = renderHook(() => useAsyncData(() => deferred.promise, []));

        act(() => {
            deferred.reject(error);
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.data).toBeUndefined();
        expect(result.current.error).toBe('boom');
    });
});
