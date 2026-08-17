// src/pages/DashboardViewPage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const API_URL = "http://localhost:5000/api";

const DashboardViewPage = () => {
    const navigate = useNavigate();
    const { dashboardId } = useParams();

    // ==========================================================
    // STATE
    // ==========================================================

    const [dashboard, setDashboard] = useState(null);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // ==========================================================
    // TOKEN
    // ==========================================================

    const getToken = () => {
        return (
            localStorage.getItem("token") ||
            localStorage.getItem("access_token")
        );
    };

    // ==========================================================
    // CHARGER LE DASHBOARD
    // ==========================================================

    useEffect(() => {
        const fetchDashboard = async () => {
            if (!dashboardId) {
                setError("Identifiant du dashboard manquant.");
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                setError("");

                const token = getToken();

                const response = await fetch(
                    `${API_URL}/dashboards/${dashboardId}`,
                    {
                        method: "GET",

                        headers: {
                            "Content-Type": "application/json",

                            ...(token
                                ? {
                                      Authorization: `Bearer ${token}`,
                                  }
                                : {}),
                        },
                    }
                );

                if (!response.ok) {
                    let errorData = {};

                    try {
                        errorData = await response.json();
                    } catch {
                        errorData = {};
                    }

                    throw new Error(
                        errorData?.message ||
                        errorData?.error ||
                        `Erreur HTTP ${response.status}`
                    );
                }

                const data = await response.json();

                /*
                 * Le backend peut retourner directement :
                 *
                 * {
                 *     id: "...",
                 *     name: "...",
                 *     ...
                 * }
                 *
                 * ou :
                 *
                 * {
                 *     dashboard: {...}
                 * }
                 */

                const dashboardData =
                    data?.dashboard ||
                    data?.data ||
                    data;

                setDashboard(dashboardData);

            } catch (err) {
                console.error(
                    "Erreur chargement dashboard :",
                    err
                );

                setError(
                    err.message ||
                    "Impossible de charger le dashboard."
                );
            } finally {
                setLoading(false);
            }
        };

        fetchDashboard();
    }, [dashboardId]);

    // ==========================================================
    // RETOUR
    // ==========================================================

    const handleBack = () => {
        navigate(-1);
    };

    // ==========================================================
    // MODIFIER LE DASHBOARD
    // ==========================================================

    const handleEdit = () => {
        navigate(
            `/dashboard/${dashboardId}/edit`
        );
    };

    // ==========================================================
    // LOADING
    // ==========================================================

    if (loading) {
        return (
            <div className="page-container">

                <div className="loading-center">

                    <div className="loading-spinner"></div>

                    <p>
                        Chargement du dashboard...
                    </p>

                </div>

            </div>
        );
    }

    // ==========================================================
    // ERROR
    // ==========================================================

    if (error) {
        return (
            <div className="page-container">

                <div className="page-header">

                    <div>
                        <h1>
                            Dashboard
                        </h1>

                        <p>
                            Impossible de charger les données.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={handleBack}
                    >
                        Retour
                    </button>

                </div>

                <div className="card">

                    <div className="alert alert-error">
                        {error}
                    </div>

                </div>

            </div>
        );
    }

    // ==========================================================
    // DASHBOARD ABSENT
    // ==========================================================

    if (!dashboard) {
        return (
            <div className="page-container">

                <div className="card">

                    <h2>
                        Dashboard introuvable
                    </h2>

                    <p>
                        Aucun dashboard correspondant à cet
                        identifiant n'a été trouvé.
                    </p>

                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={handleBack}
                    >
                        Retour
                    </button>

                </div>

            </div>
        );
    }

    // ==========================================================
    // DONNÉES DASHBOARD
    // ==========================================================

    const name =
        dashboard.name ||
        dashboard.title ||
        "Dashboard sans nom";

    const description =
        dashboard.description ||
        "Aucune description disponible.";

    const type =
        dashboard.type ||
        "standard";

    const status =
        dashboard.status ||
        "active";

    const kpis =
        Array.isArray(dashboard.kpis)
            ? dashboard.kpis
            : [];

    const charts =
        Array.isArray(dashboard.charts)
            ? dashboard.charts
            : [];

    const statistics =
        dashboard.statistics ||
        dashboard.stats ||
        {};

    // ==========================================================
    // FORMATTER UNE VALEUR
    // ==========================================================

    const formatValue = (value) => {
        if (value === null || value === undefined) {
            return "-";
        }

        if (typeof value === "number") {
            return value.toLocaleString("fr-FR");
        }

        return String(value);
    };

    // ==========================================================
    // RENDER
    // ==========================================================

    return (
        <div className="page-container">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header">

                <div>

                    <h1>
                        {name}
                    </h1>

                    <p>
                        {description}
                    </p>

                </div>

                <div
                    className="page-header-actions"
                >

                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={handleBack}
                    >
                        Retour
                    </button>

                    <button
                        type="button"
                        className="btn btn-primary"
                        onClick={handleEdit}
                    >
                        Modifier
                    </button>

                </div>

            </div>


            {/* ==================================================
                INFORMATIONS
            ================================================== */}

            <div className="dashboard-info-grid">

                <div className="card">

                    <h3>
                        Type
                    </h3>

                    <p>
                        {type}
                    </p>

                </div>

                <div className="card">

                    <h3>
                        Statut
                    </h3>

                    <p>
                        {status}
                    </p>

                </div>

                <div className="card">

                    <h3>
                        Identifiant
                    </h3>

                    <p>
                        {dashboard.id || dashboardId}
                    </p>

                </div>

            </div>


            {/* ==================================================
                KPI
            ================================================== */}

            <section className="dashboard-section">

                <div className="section-header">

                    <div>

                        <h2>
                            Indicateurs clés
                        </h2>

                        <p>
                            Principales métriques du dashboard.
                        </p>

                    </div>

                </div>


                {kpis.length > 0 ? (

                    <div className="kpi-grid">

                        {kpis.map((kpi, index) => (

                            <div
                                className="card kpi-card"
                                key={
                                    kpi.id ||
                                    kpi.key ||
                                    index
                                }
                            >

                                <h3>
                                    {
                                        kpi.label ||
                                        kpi.name ||
                                        `KPI ${index + 1}`
                                    }
                                </h3>

                                <div className="kpi-value">

                                    {formatValue(
                                        kpi.value
                                    )}

                                </div>

                                {kpi.unit && (
                                    <span>
                                        {kpi.unit}
                                    </span>
                                )}

                            </div>

                        ))}

                    </div>

                ) : (

                    <div className="card">

                        <p>
                            Aucun KPI disponible pour ce
                            dashboard.
                        </p>

                    </div>

                )}

            </section>


            {/* ==================================================
                STATISTIQUES
            ================================================== */}

            {Object.keys(statistics).length > 0 && (

                <section className="dashboard-section">

                    <div className="section-header">

                        <div>

                            <h2>
                                Statistiques
                            </h2>

                            <p>
                                Résumé des données analysées.
                            </p>

                        </div>

                    </div>

                    <div className="stats-grid">

                        {Object.entries(statistics).map(
                            ([key, value]) => (

                                <div
                                    className="card"
                                    key={key}
                                >

                                    <h3>
                                        {key}
                                    </h3>

                                    <p>
                                        {formatValue(value)}
                                    </p>

                                </div>

                            )
                        )}

                    </div>

                </section>

            )}


            {/* ==================================================
                GRAPHIQUES
            ================================================== */}

            <section className="dashboard-section">

                <div className="section-header">

                    <div>

                        <h2>
                            Visualisations
                        </h2>

                        <p>
                            Graphiques et analyses du dashboard.
                        </p>

                    </div>

                </div>


                {charts.length > 0 ? (

                    <div className="charts-grid">

                        {charts.map((chart, index) => (

                            <div
                                className="card chart-card"
                                key={
                                    chart.id ||
                                    chart.key ||
                                    index
                                }
                            >

                                <h3>
                                    {
                                        chart.title ||
                                        chart.name ||
                                        `Graphique ${index + 1}`
                                    }
                                </h3>

                                <div className="chart-placeholder">

                                    <p>
                                        Type :
                                        {" "}
                                        {
                                            chart.type ||
                                            "graphique"
                                        }
                                    </p>

                                    <p>
                                        La visualisation sera
                                        affichée ici.
                                    </p>

                                </div>

                            </div>

                        ))}

                    </div>

                ) : (

                    <div className="card">

                        <p>
                            Aucun graphique disponible pour
                            ce dashboard.
                        </p>

                    </div>

                )}

            </section>


            {/* ==================================================
                INFORMATIONS BRUTES
            ================================================== */}

            <section className="dashboard-section">

                <div className="section-header">

                    <div>

                        <h2>
                            Informations du dashboard
                        </h2>

                    </div>

                </div>

                <div className="card">

                    <pre
                        style={{
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                            overflowX: "auto",
                        }}
                    >
                        {JSON.stringify(
                            dashboard,
                            null,
                            2
                        )}
                    </pre>

                </div>

            </section>

        </div>
    );
};

export default DashboardViewPage;