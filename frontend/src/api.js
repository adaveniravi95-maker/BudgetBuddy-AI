const API =
    import.meta.env.VITE_API_URL ||
    (import.meta.env.DEV
        ? "http://127.0.0.1:8000/api"
        : "https://budgetbuddy-student-finance-platform.onrender.com/api");

export async function api(path, options = {}) {
    const token = localStorage.getItem("token");

    const isFormData = options.body instanceof FormData;
    const isUrlEncoded = options.body instanceof URLSearchParams;

    const headers = {
        ...(isFormData || isUrlEncoded
            ? {}
            : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
    };

    const response = await fetch(API + path, {
        ...options,
        headers,
    });

    const text = await response.text();

    let data = null;

    if (text) {
        try {
            data = JSON.parse(text);
        } catch {
            data = text;
        }
    }

    if (!response.ok) {
        let message = "Request failed";

        if (Array.isArray(data?.detail)) {
            message = data.detail
                .map(error => error.msg || "Invalid input")
                .join(", ");
        } else if (typeof data?.detail === "string") {
            message = data.detail;
        } else if (typeof data?.message === "string") {
            message = data.message;
        }

        throw new Error(message);
    }

    return data;
}

export function saveToken(token) {
    localStorage.setItem("token", token);
}

export function getToken() {
    return localStorage.getItem("token");
}

export function removeToken() {
    localStorage.removeItem("token");
}