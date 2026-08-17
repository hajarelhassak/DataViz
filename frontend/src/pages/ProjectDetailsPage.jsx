// src/pages/ProjectDetailsPage.jsx

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const API_URL = "/api";

const ProjectDetailsPage = () => {
    const { projectId } = useParams();
    const navigate = useNavigate();

    const [project, setProject] = useState(null);
    const [dashboards, setDashboards] = useState([]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // ==========================================================
    // CHARGER LE PROJET
    // ==========================================================

    useEffect(() => {
        const loadProject = async () => {

            try {
                setLoading(true);
                setError("");

                const token =
                    localStorage.getItem("token");

                const headers = {
                    Accept: "application/json",
                };

                if (token) {
                    headers.Authorization =
                        `Bearer ${token}`;
                }

                // ==================================================
                // VERIFICATION PROJECT ID
                // ==================================================

                if (!projectId) {
                    throw new Error(
                        "Identifiant du projet manquant."
                    );
                }

                // ==================================================
                // PROJET
                // ==================================================

                const projectResponse =
                    await fetch(
                        `${API_URL}/projects/${projectId}`,
                        {
                            method: "GET",
                            headers,
                        }
                    );

                const projectText =
                    await projectResponse.text();

                let projectData = null;

                if (projectText) {
                    try {
                        projectData =
                            JSON.parse(projectText);
                    } catch {
                        console.error(
                            "Réponse projet non JSON :",
                            projectText
                        );

                        throw new Error(
                            `Réponse serveur invalide (${projectResponse.status}).`
                        );
                    }
                }

                console.log(
                    "GET /api/projects/:id",
                    {
                        status:
                            projectResponse.status,
                        data: projectData,
                    }
                );

                if (!projectResponse.ok) {
                    throw new Error(
                        projectData?.error ||
                        projectData?.message ||
                        "Projet introuvable."
                    );
                }

                setProject(
                    projectData
                );

                // ==================================================
                // DASHBOARDS DU PROJET
                // ==================================================

                const dashboardsResponse =
                    await fetch(
                        `${API_URL}/dashboards/project/${projectId}`,
                        {
                            method: "GET",
                            headers,
                        }
                    );

                const dashboardsText =
                    await dashboardsResponse.text();

                let dashboardsData = null;

                if (dashboardsText) {
                    try {
                        dashboardsData =
                            JSON.parse(
                                dashboardsText
                            );
                    } catch {
                        console.error(
                            "Réponse dashboards non JSON :",
                            dashboardsText
                        );

                        throw new Error(
                            `Réponse dashboards invalide (${dashboardsResponse.status}).`
                        );
                    }
                }

                console.log(
                    "GET /api/dashboards/project/:id",
                    {
                        status:
                            dashboardsResponse.status,
                        data:
                            dashboardsData,
                    }
                );

                if (!dashboardsResponse.ok) {
                    /*
                     * IMPORTANT :
                     *
                     * Si ton endpoint dashboard n'existe
                     * pas encore, on ne bloque pas toute
                     * la page du projet.
                     *
                     * On considère simplement qu'il n'y
                     * a actuellement aucun dashboard.
                     */

                    if (
                        dashboardsResponse.status === 404
                    ) {
                        console.warn(
                            "Endpoint dashboards non disponible."
                        );

                        setDashboards([]);
                    } else {
                        throw new Error(
                            dashboardsData?.error ||
                            dashboardsData?.message ||
                            "Impossible de récupérer les dashboards."
                        );
                    }

                } else {

                    setDashboards(
                        Array.isArray(
                            dashboardsData
                        )
                            ? dashboardsData
                            : dashboardsData?.dashboards ||
                              []
                    );
                }

            } catch (err) {

                console.error(
                    "Erreur consultation projet :",
                    err
                );

                setError(
                    err.message ||
                    "Impossible de charger le projet."
                );

            } finally {
                setLoading(false);
            }
        };

        loadProject();

    }, [projectId]);

    // ==========================================================
    // LOADING
    // ==========================================================

    if (loading) {
        return (
            <div className="page-container">

                <p>
                    Chargement du projet...
                </p>

            </div>
        );
    }

    // ==========================================================
    // ERREUR
    // ==========================================================

    if (error) {
        return (
            <div className="page-container">

                <div className="error-message">
                    {error}
                </div>

                <button
                    type="button"
                    className="secondary-btn"
                    onClick={() =>
                        navigate("/projects")
                    }
                >
                    Retour aux projets
                </button>

            </div>
        );
    }

    // ==========================================================
    // PAGE
    // ==========================================================

    return (
        <div className="page-container">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header">

                <button
                    type="button"
                    className="secondary-btn"
                    onClick={() =>
                        navigate("/projects")
                    }
                >
                    ← Retour aux projets
                </button>

                <h1>
                    {project?.nom ||
                        "Projet"}
                </h1>

                <p>
                    Consultation du projet et
                    de ses dashboards.
                </p>

            </div>

            {/* ==================================================
                INFORMATIONS PROJET
            ================================================== */}

            <div className="card">

                <h2>
                    Informations du projet
                </h2>

                <p>
                    <strong>
                        Nom :
                    </strong>{" "}
                    {project?.nom ||
                        "—"}
                </p>

                <p>
                    <strong>
                        Entreprise :
                    </strong>{" "}
                    {project?.entreprise ||
                        "—"}
                </p>

                <p>
                    <strong>
                        Créé le :
                    </strong>{" "}
                    {project?.created_at
                        ? new Date(
                            project.created_at
                        ).toLocaleDateString(
                            "fr-FR"
                        )
                        : "—"
                    }
                </p>

            </div>

            {/* ==================================================
                DASHBOARDS
            ================================================== */}

            <div className="card">

                <div className="card-title">

                    <h2>
                        Dashboards du projet
                    </h2>

                    <span>
                        {dashboards.length}
                    </span>

                </div>

                {dashboards.length === 0 ? (

                    <div className="empty-state">

                        <h3>
                            Aucun dashboard
                        </h3>

                        <p>
                            Aucun dashboard n'a
                            encore été créé
                            pour ce projet.
                        </p>

                        <button
                            type="button"
                            className="primary-btn"
                            onClick={() =>
                                navigate(
                                    `/workspace/${projectId}`
                                )
                            }
                        >
                            Ouvrir le Workspace
                        </button>

                    </div>

                ) : (

                    <div className="dashboard-list">

                        {dashboards.map(
                            (dashboard) => (

                                <div
                                    className="dashboard-row"
                                    key={dashboard.id}
                                >

                                    <div>

                                        <h3>
                                            {
                                                dashboard.nom ||
                                                dashboard.name ||
                                                "Dashboard"
                                            }
                                        </h3>

                                        <small>
                                            {
                                                dashboard.created_at
                                                    ? `Créé le ${new Date(
                                                        dashboard.created_at
                                                    ).toLocaleDateString(
                                                        "fr-FR"
                                                    )}`
                                                    : ""
                                            }
                                        </small>

                                    </div>

                                    <button
                                        type="button"
                                        className="primary-btn"
                                        onClick={() =>
                                            navigate(
                                                `/dashboard/${dashboard.id}`
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

        </div>
    );
};

export default ProjectDetailsPage;