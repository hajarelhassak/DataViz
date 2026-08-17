// src/pages/ProjectsPage.jsx

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "/api/projects";

const ProjectsPage = () => {
    const navigate = useNavigate();

    // ==========================================================
    // ETATS
    // ==========================================================

    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);

    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const [newProject, setNewProject] = useState({
        nom: "",
    });

    // ==========================================================
    // CHARGER LES PROJETS
    // ==========================================================

    const loadProjects = async () => {
        try {
            setLoading(true);
            setError("");

            const response = await fetch(API_URL, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                },
            });

            const text = await response.text();

            let data = null;

            try {
                data = text ? JSON.parse(text) : null;
            } catch (parseError) {
                console.error(
                    "Réponse non JSON reçue par /api/projects :",
                    text
                );

                throw new Error(
                    `Le serveur a retourné une réponse invalide (${response.status}).`
                );
            }

            console.log("GET /api/projects :", {
                status: response.status,
                data,
            });

            if (!response.ok) {
                throw new Error(
                    data?.error ||
                    data?.message ||
                    `Erreur serveur (${response.status})`
                );
            }

            const projectList = Array.isArray(data)
                ? data
                : data?.projects || [];

            setProjects(projectList);

        } catch (err) {
            console.error(
                "Erreur chargement projets :",
                err
            );

            setError(
                err.message ||
                "Impossible de charger les projets."
            );

        } finally {
            setLoading(false);
        }
    };

    // ==========================================================
    // INITIALISATION
    // ==========================================================

    useEffect(() => {
        loadProjects();
    }, []);

    // ==========================================================
    // CHANGEMENT FORMULAIRE
    // ==========================================================

    const handleChange = (event) => {
        setNewProject({
            ...newProject,
            [event.target.name]: event.target.value,
        });

        setMessage("");
        setError("");
    };

    // ==========================================================
    // CREER PROJET
    // ==========================================================

    const createProject = async () => {
        const nom = newProject.nom.trim();

        if (!nom) {
            setMessage(
                "Le nom du projet est obligatoire."
            );
            return;
        }

        try {
            setCreating(true);
            setMessage("");
            setError("");

            const response = await fetch(API_URL, {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                },

                body: JSON.stringify({
                    nom,
                }),
            });

            const text = await response.text();

            let data = null;

            try {
                data = text ? JSON.parse(text) : null;
            } catch {
                console.error(
                    "Réponse création projet non JSON :",
                    text
                );

                throw new Error(
                    `Réponse serveur invalide (${response.status}).`
                );
            }

            console.log(
                "POST /api/projects :",
                {
                    status: response.status,
                    data,
                }
            );

            if (!response.ok) {
                setMessage(
                    data?.error ||
                    data?.message ||
                    `Erreur lors de la création (${response.status}).`
                );

                return;
            }

            // Réinitialiser le formulaire
            setNewProject({
                nom: "",
            });

            setMessage(
                "Projet créé avec succès."
            );

            // Recharger les projets
            await loadProjects();

            // Ouvrir automatiquement le workspace
            if (data?.id) {
                navigate(
                    `/workspace/${data.id}`
                );
            }

        } catch (err) {
            console.error(
                "Erreur création projet :",
                err
            );

            setMessage(
                err.message ||
                "Impossible de contacter le serveur."
            );

        } finally {
            setCreating(false);
        }
    };

    // ==========================================================
    // SUPPRIMER PROJET
    // ==========================================================

    const deleteProject = async (projectId) => {
        if (!projectId) {
            setMessage("Projet invalide.");
            return;
        }

        const confirmed = window.confirm(
            "Voulez-vous vraiment supprimer ce projet ?\n\n" +
            "Ses connexions, KPI et dashboards associés " +
            "pourront également être supprimés."
        );

        if (!confirmed) {
            return;
        }

        try {
            setMessage("");
            setError("");

            const response = await fetch(
                `${API_URL}/${projectId}`,
                {
                    method: "DELETE",

                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            const text = await response.text();

            let data = null;

            try {
                data = text ? JSON.parse(text) : null;
            } catch {
                console.error(
                    "Réponse suppression non JSON :",
                    text
                );

                throw new Error(
                    `Réponse serveur invalide (${response.status}).`
                );
            }

            console.log(
                "DELETE /api/projects/:id :",
                {
                    status: response.status,
                    data,
                }
            );

            if (!response.ok) {
                setMessage(
                    data?.error ||
                    data?.message ||
                    "Impossible de supprimer le projet."
                );

                return;
            }

            // Retirer le projet immédiatement de l'interface
            setProjects((currentProjects) =>
                currentProjects.filter(
                    (project) =>
                        String(project.id) !==
                        String(projectId)
                )
            );

            setMessage(
                "Projet supprimé."
            );

        } catch (err) {
            console.error(
                "Erreur suppression projet :",
                err
            );

            setMessage(
                err.message ||
                "Impossible de contacter le serveur."
            );
        }
    };

    // ==========================================================
    // OUVRIR WORKSPACE
    // ==========================================================

    const openProject = (projectId) => {
        if (!projectId) {
            setMessage(
                "Projet invalide."
            );
            return;
        }

        navigate(
            `/workspace/${projectId}`
        );
    };

    // ==========================================================
    // CONSULTER PROJET
    // ==========================================================

    const viewProject = (projectId) => {
        if (!projectId) {
            setMessage(
                "Projet invalide."
            );
            return;
        }

        navigate(
            `/projects/${projectId}`
        );
    };

    // ==========================================================
    // RENDER
    // ==========================================================

    return (
        <div className="page-container projects-page">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header projects-header">

                <h1>
                    Vos projets
                </h1>

                <p>
                    Créez et gérez vos espaces
                    d'analyse de données.
                </p>

            </div>

            {/* ==================================================
                ERREUR
            ================================================== */}

            {error && (
                <div className="status-message error">
                    {error}
                </div>
            )}

            {/* ==================================================
                LAYOUT
            ================================================== */}

            <div className="projects-layout">

                {/* ==================================================
                    CREATION
                ================================================== */}

                <div className="card">

                    <div className="card-title">

                        <h2>
                            Nouveau projet
                        </h2>

                    </div>

                    <div className="form-group">

                        <label htmlFor="project-name">
                            Nom du projet
                        </label>

                        <input
                            id="project-name"
                            name="nom"
                            type="text"
                            placeholder="Ex : Analyse commerciale"
                            value={newProject.nom}
                            onChange={handleChange}
                            disabled={creating}
                        />

                    </div>

                    <button
                        type="button"
                        className="primary-btn"
                        onClick={createProject}
                        disabled={creating}
                    >
                        {creating
                            ? "Création..."
                            : "Créer le projet"
                        }
                    </button>

                    {message && (
                        <p className="status-message">
                            {message}
                        </p>
                    )}

                </div>

                {/* ==================================================
                    LISTE DES PROJETS
                ================================================== */}

                <div className="card">

                    <div className="card-title">

                        <h2>
                            Projets existants
                        </h2>

                        <span>
                            {projects.length}
                        </span>

                    </div>

                    {/* LOADING */}

                    {loading ? (

                        <div className="empty-state">
                            <p>
                                Chargement des projets...
                            </p>
                        </div>

                    ) : projects.length === 0 ? (

                        /* AUCUN PROJET */

                        <div className="empty-state">

                            <h3>
                                Aucun projet
                            </h3>

                            <p>
                                Créez votre premier
                                espace d'analyse.
                            </p>

                        </div>

                    ) : (

                        /* LISTE */

                        <div className="projects-list">

                            {projects.map((project) => (

                                <div
                                    className="project-item"
                                    key={project.id}
                                >

                                    <div className="project-info">

                                        <h3>
                                            {project.nom}
                                        </h3>

                                        <small>
                                            Créé le{" "}
                                            {project.created_at
                                                ? new Date(
                                                    project.created_at
                                                ).toLocaleDateString(
                                                    "fr-FR"
                                                )
                                                : "—"
                                            }
                                        </small>

                                        {project.entreprise && (
                                            <small>
                                                Entreprise :{" "}
                                                {project.entreprise}
                                            </small>
                                        )}

                                    </div>

                                    <div className="project-actions">

                                        <button
                                            type="button"
                                            className="secondary-btn"
                                            onClick={() =>
                                                openProject(
                                                    project.id
                                                )
                                            }
                                        >
                                            Ouvrir
                                        </button>

                                        <button
                                            type="button"
                                            className="secondary-btn"
                                            onClick={() =>
                                                viewProject(
                                                    project.id
                                                )
                                            }
                                        >
                                            Consulter
                                        </button>

                                        <button
                                            type="button"
                                            className="secondary-btn"
                                            onClick={() =>
                                                deleteProject(
                                                    project.id
                                                )
                                            }
                                        >
                                            Supprimer
                                        </button>

                                    </div>

                                </div>

                            ))}

                        </div>

                    )}

                </div>

            </div>

        </div>
    );
};

export default ProjectsPage;