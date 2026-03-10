export const isDevelopment = process.env.NODE_ENV === "development";

export const API_CONFIG = {
    baseUrl: isDevelopment ? "http://localhost:9000" : "",
};

export const BASE_URL = API_CONFIG.baseUrl;
