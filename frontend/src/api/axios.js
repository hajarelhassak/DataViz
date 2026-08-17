// src/api/axios.js

import axios from "axios";


// =========================================================
// INSTANCE AXIOS
// =========================================================

const api = axios.create({
    baseURL: "/api",
    timeout: 120000,

    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});


// =========================================================
// REQUEST INTERCEPTOR
// =========================================================

api.interceptors.request.use(
    (config) => {

        const token = localStorage.getItem("token");

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },

    (error) => {
        return Promise.reject(error);
    }
);


// =========================================================
// RESPONSE INTERCEPTOR
// =========================================================

api.interceptors.response.use(

    (response) => {
        return response;
    },

    (error) => {

        if (error.response) {

            console.error(
                "API Error:",
                error.response.status,
                error.response.data
            );

        } else if (error.request) {

            console.error(
                "API Error: aucune réponse du serveur",
                error.message
            );

        } else {

            console.error(
                "API Error:",
                error.message
            );
        }


        // Si JWT invalide/expiré
        if (
            error.response?.status === 401 &&
            !error.config?.url?.includes("/auth/login")
        ) {

            localStorage.removeItem("token");
            localStorage.removeItem("refresh_token");
            localStorage.removeItem("user");

            window.location.hash = "#/login";
        }


        return Promise.reject(error);
    }
);


// =========================================================
// EXPORT PAR DÉFAUT
// =========================================================

export default api;