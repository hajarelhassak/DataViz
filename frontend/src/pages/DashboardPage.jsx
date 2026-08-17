// src/pages/DashboardPage.jsx

import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useProject } from "../context/ProjectContext";

// ==========================================================
// API
// ==========================================================

// IMPORTANT : ne pas mettre de Markdown ici.
// Vite proxy doit gérer /api vers Flask.
const API_URL = "/api";

// ==========================================================
// VALEURS PAR DEFAUT
// ==========================================================

const EMPTY_STATS = {
    projects: 0,
    connections: 0,
    kpis: 0,
    analyses: 0,
};

// ==========================================================
// LIRE UNE REPONSE HTTP
// ==========================================================

const readResponse = async (response) => {
    const contentType =
        response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        try {
            return await response.json();
        } catch (error) {
            console.error(
                "Impossible de lire la réponse JSON :",
                error
            );

            return {};
        }
    }

    const text = await response.text();

    console.error(
        "Réponse serveur non JSON :",
        response.status,
        text
    );

    return {
        error:
            text ||
            `Réponse serveur non JSON (${response.status})`,
    };
};

// ==========================================================
// EXTRAIRE UNE LISTE
// ==========================================================

const extractArray = (data, keys = []) => {
    if (Array.isArray(data)) {
        return data;
    }

    if (!data || typeof data !== "object") {
        return [];
    }

    for (const key of keys) {
        if (Array.isArray(data[key])) {
            return data[key];
        }
    }

    return [];
};

// ==========================================================
// NORMALISER UN DASHBOARD
// ==========================================================

const normalizeDashboard = (dashboard, index = 0) => {
    if (!dashboard || typeof dashboard !== "object") {
        return null;
    }

    const id =
        dashboard.id ||
        dashboard.dashboard_id ||
        `local-dashboard-${index}`;

    const title =
        dashboard.title ||
        dashboard.nom ||
        dashboard.name ||
        `Dashboard ${index + 1}`;

    const type =
        dashboard.type ||
        "Analyse IA";

    const date =
        dashboard.date ||
        (
            dashboard.created_at
                ? String(
                    dashboard.created_at
                ).split("T")[0]
                : "Date inconnue"
        );

    return {
        ...dashboard,

        id,
        title,
        nom:
            dashboard.nom ||
            title,

        type,

        date,

        created_at:
            dashboard.created_at ||
            null,

        kpi_count:
            Number(
                dashboard.kpi_count || 0
            ),
    };
};

// ==========================================================
// CHARGER LES DASHBOARDS LOCAUX
// ==========================================================

const loadLocalDashboards = () => {
    try {
        const stored =
            localStorage.getItem(
                "dataviz_dashboards"
            );

        if (!stored) {
            return [];
        }

        const parsed =
            JSON.parse(stored);

        if (!Array.isArray(parsed)) {
            return [];
        }

        return parsed
            .map((dashboard, index) =>
                normalizeDashboard(
                    dashboard,
                    index
                )
            )
            .filter(Boolean)
            .reverse();

    } catch (error) {
        console.error(
            "Erreur lecture dashboards locaux :",
            error
        );

        return [];
    }
};

// ==========================================================
// COMPOSANT
// ==========================================================

const DashboardPage = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const { currentProject } =
        useProject();

    // ======================================================
    // ETAT
    // ======================================================

    const [stats, setStats] =
        useState(EMPTY_STATS);

    const [dashboards, setDashboards] =
        useState([]);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");

    // ======================================================
    // CHARGEMENT
    // ======================================================

    useEffect(() => {
        let cancelled = false;

        const loadDashboardData =
            async () => {
                setLoading(true);
                setError("");

                const token =
                    localStorage.getItem(
                        "token"
                    );

                if (!token) {
                    if (!cancelled) {
                        setError(
                            "Votre session a expiré. Veuillez vous reconnecter."
                        );

                        setStats(
                            EMPTY_STATS
                        );

                        setDashboards(
                            loadLocalDashboards()
                        );

                        setLoading(false);
                    }

                    return;
                }

                try {
                    // ==================================================
                    // 1. DASHBOARDS LOCAUX
                    // ==================================================

                    const localDashboards =
                        loadLocalDashboards();

                    if (!cancelled) {
                        setDashboards(
                            localDashboards
                        );
                    }

                    // ==================================================
                    // 2. PROJETS
                    // ==================================================

                    const projectsResponse =
                        await fetch(
                            `${API_URL}/projects`,
                            {
                                method: "GET",

                                headers: {
                                    Authorization:
                                        `Bearer ${token}`,
                                },
                            }
                        );

                    const projectsData =
                        await readResponse(
                            projectsResponse
                        );

                    if (
                        !projectsResponse.ok
                    ) {
                        throw new Error(
                            projectsData.error ||
                            projectsData.message ||
                            "Impossible de récupérer les projets."
                        );
                    }

                    const projects =
                        extractArray(
                            projectsData,
                            [
                                "projects",
                                "data",
                                "items",
                            ]
                        );

                    // ==================================================
                    // 3. CONNEXIONS
                    // ==================================================

                    let totalConnections = 0;

                    /*
                     * On récupère les connexions
                     * de chaque projet.
                     *
                     * Promise.all permet de faire les requêtes
                     * en parallèle au lieu de les exécuter
                     * une par une.
                     */

                    const connectionResults =
                        await Promise.all(
                            projects.map(
                                async (
                                    project
                                ) => {
                                    if (
                                        !project?.id
                                    ) {
                                        return 0;
                                    }

                                    try {
                                        const response =
                                            await fetch(
                                                `${API_URL}/connections/project/${project.id}`,
                                                {
                                                    method:
                                                        "GET",

                                                    headers: {
                                                        Authorization:
                                                            `Bearer ${token}`,
                                                    },
                                                }
                                            );

                                        if (
                                            !response.ok
                                        ) {
                                            console.warn(
                                                `Impossible de récupérer les connexions du projet ${project.id}.`
                                            );

                                            return 0;
                                        }

                                        const data =
                                            await readResponse(
                                                response
                                            );

                                        const connections =
                                            extractArray(
                                                data,
                                                [
                                                    "connections",
                                                    "data",
                                                    "items",
                                                ]
                                            );

                                        return connections.length;

                                    } catch (
                                        connectionError
                                    ) {
                                        console.warn(
                                            `Erreur récupération connexions du projet ${project.id} :`,
                                            connectionError
                                        );

                                        return 0;
                                    }
                                }
                            )
                        );

                    totalConnections =
                        connectionResults.reduce(
                            (
                                total,
                                count
                            ) =>
                                total +
                                count,
                            0
                        );

                    // ==================================================
                    // 4. KPI
                    // ==================================================

                    /*
                     * Le backend ne possède pas encore
                     * d'endpoint officiel pour compter les KPI.
                     *
                     * On ne fabrique donc pas de données.
                     */

                    const totalKpis =
                        localDashboards.reduce(
                            (
                                total,
                                dashboard
                            ) =>
                                total +
                                Number(
                                    dashboard.kpi_count ||
                                    0
                                ),
                            0
                        );

                    // ==================================================
                    // 5. ANALYSES IA
                    // ==================================================

                    /*
                     * Chaque dashboard créé après analyse IA
                     * correspond actuellement à une analyse.
                     *
                     * Cette valeur pourra être remplacée plus tard
                     * par un vrai endpoint backend.
                     */

                    const totalAnalyses =
                        localDashboards.filter(
                            (dashboard) =>
                                dashboard.ai_analysis
                        ).length;

                    // ==================================================
                    // 6. METTRE A JOUR LES STATS
                    // ==================================================

                    if (!cancelled) {
                        setStats({
                            projects:
                                projects.length,

                            connections:
                                totalConnections,

                            kpis:
                                totalKpis,

                            analyses:
                                totalAnalyses,
                        });
                    }

                } catch (err) {
                    console.error(
                        "Erreur chargement dashboard :",
                        err
                    );

                    if (!cancelled) {
                        /*
                         * Même si l'API échoue,
                         * on conserve les dashboards locaux.
                         */

                        setDashboards(
                            loadLocalDashboards()
                        );

                        setError(
                            err.message ||
                            "Impossible de charger les données du dashboard."
                        );

                        setStats({
                            projects: 0,
                            connections: 0,

                            kpis:
                                loadLocalDashboards()
                                    .reduce(
                                        (
                                            total,
                                            dashboard
                                        ) =>
                                            total +
                                            Number(
                                                dashboard.kpi_count ||
                                                0
                                            ),
                                        0
                                    ),

                            analyses:
                                loadLocalDashboards()
                                    .filter(
                                        (
                                            dashboard
                                        ) =>
                                            dashboard.ai_analysis
                                    ).length,
                        });
                    }

                } finally {
                    if (!cancelled) {
                        setLoading(false);
                    }
                }
            };

        loadDashboardData();

        return () => {
            cancelled = true;
        };

    }, []);

    // ==========================================================
    // RECHARGER LES DASHBOARDS APRÈS CREATION
    // ==========================================================

    useEffect(() => {
        /*
         * WorkspacePage redirige vers "/"
         * avec location.state.dashboardCreated = true.
         *
         * On recharge donc les dashboards locaux.
         */

        if (
            location.state?.dashboardCreated ||
            location.state?.dashboardId
        ) {
            const localDashboards =
                loadLocalDashboards();

            setDashboards(
                localDashboards
            );

            const totalKpis =
                localDashboards.reduce(
                    (
                        total,
                        dashboard
                    ) =>
                        total +
                        Number(
                            dashboard.kpi_count ||
                            0
                        ),
                    0
                );

            const totalAnalyses =
                localDashboards.filter(
                    (dashboard) =>
                        dashboard.ai_analysis
                ).length;

            setStats(
                (current) => ({
                    ...current,

                    kpis:
                        totalKpis,

                    analyses:
                        totalAnalyses,
                })
            );

            /*
             * On nettoie le state de navigation
             * pour éviter de retraiter l'événement.
             */

            navigate(
                location.pathname,
                {
                    replace: true,
                    state: {},
                }
            );
        }

    }, [
        location.state,
        location.pathname,
        navigate,
    ]);

    // ==========================================================
    // OUVRIR UN DASHBOARD
    // ==========================================================

    const openDashboard =
        (dashboard) => {
            if (!dashboard?.id) {
                return;
            }

            /*
             * Pour l'instant, le dashboard est stocké
             * dans localStorage.
             *
             * Le vrai écran /dashboard/:id pourra être
             * ajouté lorsque l'endpoint backend existera.
             */

            navigate(
                `/dashboard/${dashboard.id}`,
                {
                    state: {
                        dashboard,
                    },
                }
            );
        };

    // ==========================================================
    // ALLER AU WORKSPACE
    // ==========================================================

    const goToWorkspace =
        () => {
            if (
                currentProject?.id
            ) {
                navigate(
                    `/workspace/${currentProject.id}`
                );

                return;
            }

            navigate(
                "/projects"
            );
        };

    // ==========================================================
    // CARTES KPI
    // ==========================================================

    const cards = [
        {
            title:
                "Projets actifs",

            value:
                stats.projects,

            description:
                "Espaces d'analyse",

            icon:
                "▣",
        },

        {
            title:
                "Connexions BDD",

            value:
                stats.connections,

            description:
                "Sources connectées",

            icon:
                "◉",
        },

        {
            title:
                "KPI générés",

            value:
                stats.kpis,

            description:
                "Indicateurs calculés",

            icon:
                "◫",
        },

        {
            title:
                "Analyses IA",

            value:
                stats.analyses,

            description:
                "Analyses disponibles",

            icon:
                "✦",
        },
    ];

    // ==========================================================
    // LOADING
    // ==========================================================

    if (loading) {
        return (
            <div className="dashboard-page">

                <div className="dashboard-header">

                    <div>

                        <h1>
                            Votre espace analytique
                        </h1>

                        <p>
                            Chargement de vos données...
                        </p>

                    </div>

                </div>

            </div>
        );
    }

    // ==========================================================
    // PAGE
    // ==========================================================

    return (
        <div className="dashboard-page">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="dashboard-header">

                <div>

                    <h1>
                        Votre espace analytique
                    </h1>

                    <p>
                        Analysez vos données,
                        créez des indicateurs
                        et générez des insights.
                    </p>

                </div>

                <div>

                    <button
                        type="button"
                        className="primary-btn"
                        onClick={
                            goToWorkspace
                        }
                    >
                        Connecter une base
                    </button>

                </div>

            </div>

            {/* ==================================================
                ERREUR
            ================================================== */}

            {error && (
                <div
                    className="error-message"
                    role="alert"
                >
                    {error}
                </div>
            )}

            {/* ==================================================
                KPI CARDS
            ================================================== */}

            <div className="kpi-grid">

                {cards.map(
                    (item) => (

                        <div
                            className="kpi-card"
                            key={
                                item.title
                            }
                        >

                            <div className="kpi-icon">
                                {item.icon}
                            </div>

                            <div>

                                <span>
                                    {
                                        item.title
                                    }
                                </span>

                                <h2>
                                    {
                                        item.value
                                    }
                                </h2>

                                <small>
                                    {
                                        item.description
                                    }
                                </small>

                            </div>

                        </div>
                    )
                )}

            </div>

            {/* ==================================================
                CONTENT
            ================================================== */}

            <div className="dashboard-content">

                {/* ==================================================
                    DASHBOARDS
                ================================================== */}

                <div className="panel">

                    <div className="panel-title">

                        <h2>
                            Dashboards récents
                        </h2>

                        <button
                            type="button"
                            className="primary-btn"
                            onClick={
                                goToWorkspace
                            }
                        >
                            + Nouveau dashboard
                        </button>

                    </div>

                    {dashboards.length === 0 ? (

                        <div className="empty-state">

                            <h3>
                                Aucun dashboard
                            </h3>

                            <p>
                                Créez votre premier
                                dashboard après avoir
                                connecté une source
                                de données.
                            </p>

                            <button
                                type="button"
                                className="secondary-btn"
                                onClick={
                                    goToWorkspace
                                }
                            >
                                Connecter une base
                            </button>

                        </div>

                    ) : (

                        <div>

                            {dashboards.map(
                                (
                                    dashboard
                                ) => (

                                    <div
                                        className="dashboard-row"
                                        key={
                                            dashboard.id
                                        }
                                    >

                                        <div>

                                            <h3>
                                                {
                                                    dashboard.title
                                                }
                                            </h3>

                                            <p>
                                                {
                                                    dashboard.type
                                                }

                                                {dashboard.table && (
                                                    <>
                                                        {" — Table : "}
                                                        {
                                                            dashboard.table
                                                        }
                                                    </>
                                                )}
                                            </p>

                                            <small>
                                                Créé le{" "}
                                                {
                                                    dashboard.date
                                                }

                                                {" — "}

                                                {
                                                    dashboard.kpi_count
                                                }

                                                {" KPI"}
                                            </small>

                                        </div>

                                        <button
                                            type="button"
                                            className="secondary-btn"
                                            onClick={() =>
                                                openDashboard(
                                                    dashboard
                                                )
                                            }
                                        >
                                            Ouvrir
                                        </button>

                                    </div>

                                )
                            )}

                        </div>

                    )}

                </div>

                {/* ==================================================
                    IA PANEL
                ================================================== */}

                <div className="panel ai-panel">

                    <div className="ai-circle">
                        AI
                    </div>

                    <h2>
                        Assistant IA
                    </h2>

                    <p>
                        L'assistant analyse le
                        schéma de vos sources et
                        propose des recommandations
                        à partir des données
                        sélectionnées.
                    </p>

                    <div className="ai-number">

                        {stats.analyses}

                        <span>
                            analyses disponibles
                        </span>

                    </div>

                    <button
                        type="button"
                        className="primary-btn"
                        onClick={() =>
                            navigate(
                                "/ai"
                            )
                        }
                    >
                        Consulter
                    </button>

                </div>

            </div>

        </div>
    );
};

export default DashboardPage;