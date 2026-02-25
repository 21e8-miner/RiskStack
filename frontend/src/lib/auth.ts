export const tokenKey = "riskstack_token";

export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(tokenKey);
}

export function setToken(t: string) {
    localStorage.setItem(tokenKey, t);
}

export function clearToken() {
    localStorage.removeItem(tokenKey);
}
