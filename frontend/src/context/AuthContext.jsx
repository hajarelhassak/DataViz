// src/context/AuthContext.jsx

import {
    createContext,
    useState,
    useContext,
    useEffect,
} from "react";

import { authApi } from "../api/auth";


const AuthContext = createContext(null);


// =========================================================
// HOOK useAuth
// =========================================================

export const useAuth = () => {

    const context = useContext(AuthContext);

    if (!context) {
        throw new Error(
            "useAuth must be used within AuthProvider"
        );
    }

    return context;
};


// =========================================================
// AUTH PROVIDER
// =========================================================

export const AuthProvider = ({ children }) => {

    const [user, setUser] = useState(null);

    const [loading, setLoading] = useState(true);

    const [isAuthenticated, setIsAuthenticated] =
        useState(false);


    // =====================================================
    // RESTAURATION SESSION
    // =====================================================

    useEffect(() => {

        const token =
            localStorage.getItem("token");

        const storedUser =
            localStorage.getItem("user");


        if (!token) {

            setLoading(false);
            return;
        }


        if (storedUser) {

            try {

                const parsedUser =
                    JSON.parse(storedUser);

                setUser(parsedUser);

                setIsAuthenticated(true);

            } catch (error) {

                console.error(
                    "Utilisateur local invalide :",
                    error
                );

                authApi.logout();

                setUser(null);
                setIsAuthenticated(false);
            }

            setLoading(false);
            return;
        }


        /*
         * Token présent mais utilisateur absent.
         * On demande le profil au backend.
         */

        authApi.me()
            .then((response) => {

                const userData =
                    response.data;

                localStorage.setItem(
                    "user",
                    JSON.stringify(userData)
                );

                setUser(userData);
                setIsAuthenticated(true);
            })
            .catch((error) => {

                console.error(
                    "Impossible de restaurer la session :",
                    error
                );

                authApi.logout();

                setUser(null);
                setIsAuthenticated(false);
            })
            .finally(() => {

                setLoading(false);

            });

    }, []);


    // =====================================================
    // LOGIN
    // =====================================================

    const login = async (
        email,
        password
    ) => {

        const cleanEmail =
            email.trim().toLowerCase();


        if (!cleanEmail || !password) {

            throw new Error(
                "Email et mot de passe requis."
            );
        }


        console.log(
            "Tentative de connexion :",
            cleanEmail
        );


        try {

            const response =
                await authApi.login(
                    cleanEmail,
                    password
                );


            console.log(
                "Réponse login :",
                response.data
            );


            const data =
                response.data || {};


            const accessToken =
                data.access_token;

            const refreshToken =
                data.refresh_token;

            const userData =
                data.user;


            // =================================================
            // VALIDATION RÉPONSE
            // =================================================

            if (!accessToken) {

                console.error(
                    "Réponse backend sans access_token :",
                    data
                );

                throw new Error(
                    "Le serveur n'a pas retourné de token d'authentification."
                );
            }


            // =================================================
            // STOCKAGE ACCESS TOKEN
            // =================================================

            localStorage.setItem(
                "token",
                accessToken
            );


            // =================================================
            // STOCKAGE REFRESH TOKEN
            // =================================================

            if (refreshToken) {

                localStorage.setItem(
                    "refresh_token",
                    refreshToken
                );
            }


            // =================================================
            // STOCKAGE UTILISATEUR
            // =================================================

            if (userData) {

                localStorage.setItem(
                    "user",
                    JSON.stringify(userData)
                );

                setUser(userData);

            } else {

                /*
                 * Normalement ton backend retourne toujours user.
                 */

                const fallbackUser = {
                    email: cleanEmail,
                };

                localStorage.setItem(
                    "user",
                    JSON.stringify(fallbackUser)
                );

                setUser(fallbackUser);
            }


            setIsAuthenticated(true);


            return data;

        } catch (error) {

            console.error(
                "Erreur AuthContext.login :",
                error
            );

            throw error;
        }
    };


    // =====================================================
    // LOGOUT
    // =====================================================

    const logout = () => {

        authApi.logout();

        setUser(null);

        setIsAuthenticated(false);
    };


    // =====================================================
    // CONTEXT
    // =====================================================

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                isAuthenticated,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};