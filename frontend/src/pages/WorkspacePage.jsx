// src/pages/WorkspacePage.jsx

import React, { useEffect, useState } from "react";

import {
    useNavigate,
    useParams,
    useLocation,
} from "react-router-dom";


// ==========================================================
// API
// ==========================================================

const API_URL = "/api";


// ==========================================================
// STORAGE KEYS
// ==========================================================

const getConnectionStorageKey = (projectId) =>
    `dataviz_selected_connection_${projectId}`;

const getTablesStorageKey = (projectId) =>
    `dataviz_selected_tables_${projectId}`;


// ==========================================================
// COMPOSANT
// ==========================================================

const WorkspacePage = () => {

    const { projectId } = useParams();

    const navigate = useNavigate();

    const location = useLocation();


    // ==========================================================
    // PROJET
    // ==========================================================

    const [project, setProject] = useState(null);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");


    // ==========================================================
    // CONNEXION SELECTIONNEE
    // ==========================================================

    const [selectedConnectionId, setSelectedConnectionId] =
        useState(
            location.state?.connectionId ||
            null
        );


    // ==========================================================
    // TABLES SELECTIONNEES
    // ==========================================================

    const [selectedTables, setSelectedTables] =
        useState(
            Array.isArray(
                location.state?.selectedTables
            )
                ? location.state.selectedTables
                : []
        );


    // ==========================================================
    // RECUPERATION DES DONNEES DEPUIS LE STORAGE
    // ==========================================================

    useEffect(() => {

        if (!projectId) {
            return;
        }


        /*
         * Si ConnectionsPage nous a transmis les informations
         * via location.state, on les sauvegarde.
         */

        if (location.state?.connectionId) {

            setSelectedConnectionId(
                location.state.connectionId
            );


            sessionStorage.setItem(
                getConnectionStorageKey(projectId),
                location.state.connectionId
            );

        }


        if (
            Array.isArray(
                location.state?.selectedTables
            )
        ) {

            setSelectedTables(
                location.state.selectedTables
            );


            sessionStorage.setItem(
                getTablesStorageKey(projectId),
                JSON.stringify(
                    location.state.selectedTables
                )
            );

        }


        /*
         * Si la page a été rechargée, location.state est perdu.
         * On récupère donc les informations du sessionStorage.
         */

        if (
            !location.state?.connectionId
        ) {

            const storedConnectionId =
                sessionStorage.getItem(
                    getConnectionStorageKey(projectId)
                );


            if (storedConnectionId) {

                setSelectedConnectionId(
                    storedConnectionId
                );

            }

        }


        if (
            !Array.isArray(
                location.state?.selectedTables
            )
        ) {

            const storedTables =
                sessionStorage.getItem(
                    getTablesStorageKey(projectId)
                );


            if (storedTables) {

                try {

                    const parsedTables =
                        JSON.parse(
                            storedTables
                        );


                    if (
                        Array.isArray(
                            parsedTables
                        )
                    ) {

                        setSelectedTables(
                            parsedTables
                        );

                    }

                } catch (storageError) {

                    console.error(
                        "Erreur lecture tables sauvegardées :",
                        storageError
                    );

                }

            }

        }

    }, [
        projectId,
        location.state,
    ]);


    // ==========================================================
    // CHARGER LE PROJET
    // ==========================================================

    useEffect(() => {

        const loadProject = async () => {

            if (!projectId) {

                setError(
                    "Projet invalide."
                );

                setLoading(false);

                return;
            }


            const token =
                localStorage.getItem(
                    "token"
                );


            try {

                const response =
                    await fetch(
                        `${API_URL}/projects/${projectId}`,
                        {
                            method: "GET",

                            headers: {
                                ...(token
                                    ? {
                                          Authorization:
                                              `Bearer ${token}`,
                                      }
                                    : {}),
                            },
                        }
                    );


                const contentType =
                    response.headers.get(
                        "content-type"
                    ) || "";


                let data = null;


                if (
                    contentType.includes(
                        "application/json"
                    )
                ) {

                    data =
                        await response.json();

                } else {

                    const text =
                        await response.text();


                    throw new Error(
                        text ||
                        `Erreur serveur (${response.status}).`
                    );

                }


                if (!response.ok) {

                    throw new Error(
                        data?.error ||
                        data?.message ||
                        `Erreur serveur (${response.status}).`
                    );

                }


                const loadedProject =
                    data?.project ||
                    data?.data ||
                    data;


                if (
                    !loadedProject ||
                    typeof loadedProject !==
                        "object"
                ) {

                    throw new Error(
                        "Projet introuvable."
                    );

                }


                setProject(
                    loadedProject
                );

            } catch (err) {

                console.error(
                    "Erreur chargement projet :",
                    err
                );


                /*
                 * Fallback pour permettre au workspace
                 * de rester accessible.
                 */

                setProject({
                    id: projectId,
                    nom: `Projet ${projectId}`,
                });

            } finally {

                setLoading(false);

            }

        };


        loadProject();

    }, [projectId]);


    // ==========================================================
    // NAVIGATION
    // ==========================================================

    const goToProjects = () => {

        navigate(
            "/projects"
        );

    };


    // ==========================================================
    // AJOUTER UNE CONNEXION
    // ==========================================================

    const goToConnection = () => {

        navigate(
            `/workspace/${projectId}/connection`
        );

    };


    // ==========================================================
    // VOIR LES CONNEXIONS
    // ==========================================================

    const goToConnections = () => {

        navigate(
            `/connections/${projectId}`,
            {
                state: {
                    connectionId:
                        selectedConnectionId,

                    selectedTables:
                        selectedTables,
                },
            }
        );

    };


    // ==========================================================
    // CREER UN DASHBOARD
    // ==========================================================

    const goToCreateDashboard = () => {

        /*
         * Vérification importante :
         *
         * CreateDashboardPage a besoin de la connexion
         * sélectionnée pour appeler :
         *
         * /api/ai/connections/:connectionId/recommend
         */

        if (!selectedConnectionId) {

            setError(
                "Veuillez d'abord sélectionner une connexion BDD."
            );

            return;

        }


        /*
         * On transmet explicitement les informations
         * à CreateDashboardPage.
         */

        navigate(
            `/workspace/${projectId}/dashboards/create`,
            {
                state: {
                    connectionId:
                        selectedConnectionId,

                    selectedTables:
                        selectedTables,
                },
            }
        );

    };


    // ==========================================================
    // LOADING
    // ==========================================================

    if (loading) {

        return (

            <div className="page-container">

                <div className="empty-state">

                    <h3>
                        Chargement du projet...
                    </h3>

                    <p>
                        Préparation de votre workspace.
                    </p>

                </div>

            </div>

        );

    }


    // ==========================================================
    // PROJET INTROUVABLE
    // ==========================================================

    if (!project) {

        return (

            <div className="page-container">

                <div className="empty-state">

                    <h3>
                        Projet introuvable
                    </h3>

                    <p>
                        Aucun projet valide n'a été
                        fourni à cette page.
                    </p>


                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={goToProjects}
                    >
                        Retour aux projets
                    </button>

                </div>

            </div>

        );

    }


    // ==========================================================
    // NOM DU PROJET
    // ==========================================================

    const projectName =
        project.nom ||
        project.name ||
        `Projet ${projectId}`;


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
                        Workspace du projet
                    </h1>

                    <p>
                        Gérez les données et les
                        dashboards de votre projet.
                    </p>

                </div>


                <button
                    type="button"
                    className="secondary-btn"
                    onClick={goToProjects}
                >
                    Retour aux projets
                </button>

            </div>


            {/* ==================================================
                ERREUR
            ================================================== */}

            {error && (

                <div
                    className="alert alert-error"
                    style={{
                        marginBottom: "20px",
                    }}
                >
                    {error}
                </div>

            )}


            {/* ==================================================
                INFORMATIONS PROJET
            ================================================== */}

            <div className="panel">

                <div className="panel-title">

                    <div>

                        <h2>
                            Workspace
                        </h2>

                        <p>
                            Projet actif
                        </p>

                    </div>

                </div>


                <div className="card">

                    <h3>
                        {projectName}
                    </h3>

                    <p>
                        Identifiant du projet :
                        {" "}
                        {projectId}
                    </p>

                </div>

            </div>


            {/* ==================================================
                1. CONNEXIONS
            ================================================== */}

            <div className="panel">

                <div className="panel-title">

                    <div>

                        <h2>
                            Connexions aux données
                        </h2>

                        <p>
                            Connectez et gérez les sources
                            de données de votre projet.
                        </p>

                    </div>

                </div>


                {/* ==================================================
                    NOUVELLE CONNEXION
                ================================================== */}

                <div className="dashboard-row">

                    <div>

                        <h3>
                            Nouvelle connexion
                        </h3>

                        <p>
                            Connectez SQLite, MySQL,
                            PostgreSQL ou SQL Server.
                        </p>

                    </div>


                    <button
                        type="button"
                        className="primary-btn"
                        onClick={
                            goToConnection
                        }
                    >
                        Ajouter une connexion
                    </button>

                </div>


                {/* ==================================================
                    CONNEXIONS EXISTANTES
                ================================================== */}

                <div className="dashboard-row">

                    <div>

                        <h3>
                            Connexions existantes
                        </h3>

                        <p>
                            Consultez vos connexions,
                            explorez leur schéma et
                            sélectionnez les tables.
                        </p>

                    </div>


                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={
                            goToConnections
                        }
                    >
                        Voir les connexions
                    </button>

                </div>


                {/* ==================================================
                    CONNEXION SELECTIONNEE
                ================================================== */}

                <div
                    className="card"
                    style={{
                        marginTop: "20px",
                    }}
                >

                    <h3>
                        Connexion sélectionnée
                    </h3>


                    {selectedConnectionId ? (

                        <>
                            <p>
                                Une connexion BDD est
                                actuellement sélectionnée.
                            </p>


                            <p>

                                <strong>
                                    Connection ID :
                                </strong>

                                {" "}

                                {selectedConnectionId}

                            </p>


                            <p>

                                <strong>
                                    Tables sélectionnées :
                                </strong>

                                {" "}

                                {selectedTables.length}

                            </p>

                        </>

                    ) : (

                        <p>
                            Aucune connexion BDD n'est
                            actuellement sélectionnée.
                        </p>

                    )}

                </div>

            </div>


            {/* ==================================================
                2. DONNEES
            ================================================== */}

            <div className="panel">

                <div className="panel-title">

                    <div>

                        <h2>
                            Données
                        </h2>

                        <p>
                            Le traitement des données se fait
                            à partir de la connexion sélectionnée.
                        </p>

                    </div>

                </div>


                <div className="card">

                    <h3>
                        Explorer vos données
                    </h3>

                    <p>
                        Commencez par sélectionner une
                        connexion dans la liste des
                        connexions existantes.
                    </p>


                    <p>
                        Vous pourrez ensuite :
                    </p>


                    <ul>

                        <li>
                            Explorer le schéma
                        </li>

                        <li>
                            Consulter les tables
                        </li>

                        <li>
                            Consulter les colonnes
                        </li>

                        <li>
                            Sélectionner les tables
                            à analyser
                        </li>

                    </ul>


                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={
                            goToConnections
                        }
                    >
                        Gérer les connexions
                    </button>

                </div>

            </div>


            {/* ==================================================
                3. DASHBOARDS
            ================================================== */}

            <div className="panel">

                <div className="panel-title">

                    <div>

                        <h2>
                            Dashboards
                        </h2>

                        <p>
                            Créez et consultez les dashboards
                            de votre projet.
                        </p>

                    </div>

                </div>


                <div className="dashboard-row">

                    <div>

                        <h3>
                            Nouveau dashboard
                        </h3>

                        <p>
                            Configurez un dashboard à partir
                            des données sélectionnées.
                        </p>

                    </div>


                    <button
                        type="button"
                        className="primary-btn"
                        onClick={
                            goToCreateDashboard
                        }
                        disabled={
                            !selectedConnectionId
                        }
                    >
                        + Créer un dashboard
                    </button>

                </div>


                {!selectedConnectionId && (

                    <p
                        style={{
                            marginTop: "12px",
                            color: "#64748b",
                        }}
                    >
                        Sélectionnez d'abord une connexion
                        BDD et les tables à analyser.
                    </p>

                )}

            </div>


            {/* ==================================================
                4. WORKFLOW
            ================================================== */}

            <div className="panel">

                <div className="panel-title">

                    <div>

                        <h2>
                            Workflow DataViz
                        </h2>

                        <p>
                            Suivez les étapes pour construire
                            votre analyse.
                        </p>

                    </div>

                </div>


                {/* ETAPE 1 */}

                <div className="dashboard-row">

                    <div>

                        <h3>
                            1. Connexion
                        </h3>

                        <p>
                            Connectez votre source
                            de données.
                        </p>

                    </div>

                </div>


                {/* ETAPE 2 */}

                <div className="dashboard-row">

                    <div>

                        <h3>
                            2. Schéma
                        </h3>

                        <p>
                            Explorez les tables et
                            leurs colonnes.
                        </p>

                    </div>

                </div>


                {/* ETAPE 3 */}

                <div className="dashboard-row">

                    <div>

                        <h3>
                            3. Sélection des tables
                        </h3>

                        <p>
                            Sélectionnez uniquement les
                            tables nécessaires à l'analyse.
                        </p>

                    </div>

                </div>


                {/* ETAPE 4 */}

                <div className="dashboard-row">

                    <div>

                        <h3>
                            4. Dashboard
                        </h3>

                        <p>
                            Créez et visualisez votre
                            dashboard.
                        </p>

                    </div>

                </div>

            </div>

        </div>

    );

};


export default WorkspacePage;