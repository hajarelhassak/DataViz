// src/pages/LoginPage.jsx

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";


const LoginPage = () => {

    const [email, setEmail] =
        useState("admin@test.local");

    const [password, setPassword] =
        useState("admin123");

    const [error, setError] =
        useState("");

    const [loading, setLoading] =
        useState(false);


    const { login } = useAuth();

    const navigate = useNavigate();


    // =====================================================
    // SUBMIT
    // =====================================================

    const handleSubmit = async (event) => {

        event.preventDefault();

        setError("");

        setLoading(true);


        try {

            await login(
                email,
                password
            );


            navigate("/");

        } catch (err) {

            console.error(
                "Erreur connexion :",
                err
            );


            const status =
                err.response?.status;


            const backendError =
                err.response?.data?.error ||
                err.response?.data?.message;


            if (status === 400) {

                setError(
                    backendError ||
                    "Email et mot de passe requis."
                );

            } else if (status === 401) {

                setError(
                    backendError ||
                    "Email ou mot de passe incorrect."
                );

            } else if (status === 502) {

                setError(
                    "Le serveur backend est inaccessible. Vérifiez que Flask fonctionne sur le port 5000."
                );

            } else if (status >= 500) {

                setError(
                    backendError ||
                    "Une erreur interne du serveur est survenue."
                );

            } else {

                setError(
                    backendError ||
                    err.message ||
                    "Impossible de se connecter."
                );
            }

        } finally {

            setLoading(false);
        }
    };


    // =====================================================
    // UI
    // =====================================================

    return (

        <div className="login-page">

            <section className="login-showcase">

                <div className="login-logo">

                    <span className="logo-icon">
                        ◈
                    </span>

                    DataViz

                </div>


                <h2>

                    Transformez vos données
                    <br />

                    en décisions intelligentes

                </h2>


                <p>

                    Connectez vos bases de données,
                    analysez vos indicateurs clés
                    et créez des dashboards professionnels.

                </p>


                <div className="data-preview">

                    <div className="preview-card">

                        <span>
                            KPI
                        </span>

                        <strong>
                            +24.8%
                        </strong>

                        <small>
                            Performance mensuelle
                        </small>

                    </div>


                    <div className="chart-preview">

                        <div className="chart-bar bar-one" />
                        <div className="chart-bar bar-two" />
                        <div className="chart-bar bar-three" />
                        <div className="chart-bar bar-four" />

                    </div>

                </div>

            </section>


            <section className="login-container">

                <div className="login-card">

                    <div className="mobile-brand">
                        DataViz
                    </div>


                    <h1 className="login-title">
                        Bienvenue
                    </h1>


                    <p className="login-subtitle">

                        Connectez-vous à votre espace d'analyse

                    </p>


                    {error && (

                        <div
                            className="login-error"
                            role="alert"
                        >

                            {error}

                        </div>

                    )}


                    <form onSubmit={handleSubmit}>

                        <div className="form-group">

                            <label
                                className="form-label"
                                htmlFor="email"
                            >
                                Email professionnel
                            </label>


                            <input
                                id="email"
                                type="email"
                                className="form-input"
                                value={email}
                                onChange={(event) =>
                                    setEmail(event.target.value)
                                }
                                placeholder="admin@entreprise.com"
                                autoComplete="email"
                                disabled={loading}
                                required
                            />

                        </div>


                        <div className="form-group">

                            <label
                                className="form-label"
                                htmlFor="password"
                            >
                                Mot de passe
                            </label>


                            <input
                                id="password"
                                type="password"
                                className="form-input"
                                value={password}
                                onChange={(event) =>
                                    setPassword(event.target.value)
                                }
                                placeholder="••••••••"
                                autoComplete="current-password"
                                disabled={loading}
                                required
                            />

                        </div>


                        <button
                            type="submit"
                            className="btn btn-primary login-btn"
                            disabled={loading}
                        >

                            {loading
                                ? "Connexion..."
                                : "Se connecter"
                            }

                        </button>

                    </form>


                    <footer className="login-footer">

                        © 2026 DataViz. Tous droits réservés.

                    </footer>

                </div>

            </section>

        </div>
    );
};


export default LoginPage;