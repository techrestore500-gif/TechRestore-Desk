import { useEffect, useState } from "react";

export type AsyncState<T> = {
    data: T | undefined;
    loading: boolean;
    error: string | null;
};

export function useAsyncData<T>(factory: () => Promise<T>, dependencies: readonly unknown[]): AsyncState<T> {
    const [data, setData] = useState<T | undefined>(undefined);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isActive = true;
        setLoading(true);

        factory()
            .then((result) => {
                if (isActive) {
                    setData(result);
                    setError(null);
                }
            })
            .catch((requestError: unknown) => {
                if (isActive) {
                    setError(requestError instanceof Error ? requestError.message : "Request failed");
                }
            })
            .finally(() => {
                if (isActive) {
                    setLoading(false);
                }
            });

        return () => {
            isActive = false;
        };
    }, dependencies);

    return { data, loading, error };
}
