import axios from "axios";

const api = axios.create({
    baseURL: "/api",
    timeout: 120000,

    headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
    },
});


/* =========================================================
   REQUEST INTERCEPTOR
========================================================= */

api.interceptors.request.use(
    (config) => {

        const token =
            localStorage.getItem("token");

        if (token) {
            config.headers.Authorization =
                `Bearer ${token}`;
        }

        return config;
    },

    (error) => {
        return Promise.reject(error);
    }
);


/* =========================================================
   RESPONSE INTERCEPTOR
========================================================= */

api.interceptors.response.use(

    (response) => {
        return response;
    },

    (error) => {

        if (error.response) {

            console.error(
                "[API ERROR]",
                error.response.status,
                error.config?.method?.toUpperCase(),
                error.config?.url,
                error.response.data
            );

        } else if (error.request) {

            console.error(
                "[API NETWORK ERROR]",
                error.config?.method?.toUpperCase(),
                error.config?.url,
                error.message
            );

        } else {

            console.error(
                "[API CONFIG ERROR]",
                error.message
            );
        }

        return Promise.reject(error);
    }
);


export default api;