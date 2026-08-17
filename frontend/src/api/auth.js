// src/api/auth.js

import api from "./axios";


// =========================================================
// AUTH API
// =========================================================

export const authApi = {

    // =====================================================
    // LOGIN
    // =====================================================

    login(email, password) {

        return api.post(
            "/auth/login",
            {
                email: email.trim().toLowerCase(),
                password: password,
            }
        );
    },


    // =====================================================
    // REGISTER
    // =====================================================

    register(data) {

        return api.post(
            "/auth/register",
            data
        );
    },


    // =====================================================
    // REFRESH TOKEN
    // =====================================================

    refresh() {

        const refreshToken =
            localStorage.getItem("refresh_token");

        return api.post(
            "/auth/refresh",
            {},
            {
                headers: {
                    Authorization: `Bearer ${refreshToken}`,
                },
            }
        );
    },


    // =====================================================
    // CURRENT USER
    // =====================================================

    me() {

        return api.get(
            "/auth/me"
        );
    },


    // =====================================================
    // LOGOUT LOCAL
    // =====================================================

    logout() {

        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        localStorage.removeItem("current_project_id");
    },
};