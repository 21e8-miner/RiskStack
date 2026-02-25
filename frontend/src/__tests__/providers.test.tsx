import { describe, it, expect } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "../lib/api";

describe("react-query retry policy", () => {
    it("does not retry 422", () => {
        const qc = new QueryClient({
            defaultOptions: {
                queries: {
                    retry: (count, err: unknown) => {
                        if (err instanceof ApiError) {
                            if ([401, 403, 404, 422].includes(err.status)) return false;
                            if (err.message === "ZOD_SCHEMA_ERROR") return false;
                        }
                        return count < 2;
                    },
                },
            },
        });
        const retry = qc.getDefaultOptions().queries?.retry as any;
        expect(retry(0, new ApiError(422, "HTTP 422", {}))).toBe(false);
        expect(retry(0, new ApiError(500, "HTTP 500", {}))).toBe(true);
    });
});
