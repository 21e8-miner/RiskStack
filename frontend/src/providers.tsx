import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export default function Providers({ children }: { children: React.ReactNode }) {
    const [qc] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        refetchOnWindowFocus: false,
                        staleTime: 1000 * 60 * 5,
                        retry: (count, err: unknown) => {
                            const ae = err as any;
                            const isApiErrorLike =
                                ae &&
                                ae.name === "ApiError" &&
                                Number.isInteger(ae.status) &&
                                ae.status >= 400 &&
                                ae.status <= 599;

                            if (isApiErrorLike) {
                                if ([401, 403, 404, 422].includes(ae.status)) return false;
                                if (ae.message === "ZOD_SCHEMA_ERROR") return false;
                            }
                            return count < 2;
                        },
                    },
                },
            })
    );

    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
