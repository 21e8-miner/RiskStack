import { describe, it, expect } from "vitest";

describe("duck typing ApiError", () => {
    it("recognizes api error shape", () => {
        const e: any = { name: "ApiError", status: 422, message: "HTTP 422" };
        const isApiErrorLike =
            e &&
            e.name === "ApiError" &&
            Number.isInteger(e.status) &&
            e.status >= 400 &&
            e.status <= 599;
        expect(isApiErrorLike).toBe(true);
    });
});
