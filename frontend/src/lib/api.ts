import { z, ZodSchema } from "zod";
import { getToken } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export class ApiError extends Error {
    status: number;
    detail: any;

    constructor(status: number, message: string, detail?: any) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.detail = detail;
    }
}

async function fetchJson(path: string, init: RequestInit) {
    const token = getToken();
    const headers: Record<string, string> = { ...(init.headers as any) };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: "no-store" });
    const text = await res.text();

    if (!res.ok) {
        let parsed: any = null;
        try {
            parsed = JSON.parse(text);
        } catch { }
        const detail = parsed?.detail ?? parsed ?? text;
        throw new ApiError(res.status, `HTTP ${res.status}`, detail);
    }

    return text ? JSON.parse(text) : null;
}

export async function apiGetZod<T>(path: string, schema: ZodSchema<T>): Promise<T> {
    const raw = await fetchJson(path, { method: "GET" });
    const parsed = schema.safeParse(raw);
    if (!parsed.success) {
        console.error("Zod Validation Failed:", parsed.error.format());
        throw new ApiError(500, "ZOD_SCHEMA_ERROR", parsed.error.format());
    }
    return parsed.data;
}

export async function apiPostZod<T>(path: string, body: any, schema: ZodSchema<T>): Promise<T> {
    const raw = await fetchJson(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const parsed = schema.safeParse(raw);
    if (!parsed.success) {
        console.error("Zod Validation Failed:", parsed.error.format());
        throw new ApiError(500, "ZOD_SCHEMA_ERROR", parsed.error.format());
    }
    return parsed.data;
}
