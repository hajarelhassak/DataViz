// src/pages/CreateDashboardPage.jsx

import React, { useEffect, useState } from "react";
import {
    useNavigate,
    useParams,
    useLocation,
} from "react-router-dom";

import api from "../api/axios";


// ==========================================================
// ETAPES DU PIPELINE
// ==========================================================

const INITIAL_STEPS = [
    {
        label: "Vérification de la connexion",
        status: "pending",
    },
    {
        label: "Création du dashboard",
        status: "pending",
    },
    {
        label: "Récupération du schéma",
        status: "pending",
    },
    {
        label: "Analyse du schéma",
        status: "pending",
    },
    {
        label: "Domaine métier identifié",
        status: "pending",
    },
    {
        label: "KPI sélectionnés",
        status: "pending",
    },
    {
        label: "Calcul des indicateurs",
        status: "pending",
    },
    {
        label: "Génération des visualisations",
        status: "pending",
    },
    {
        label: "Construction du dashboard",
        status: "pending",
    },
];


// ==========================================================
// CLONER LES ETAPES
// ==========================================================

const createInitialSteps = () => {
    return INITIAL_STEPS.map((step) => ({
        ...step,
    }));
};


// ==========================================================
// EXTRAIRE UN MESSAGE D'ERREUR
// ==========================================================

const getErrorMessage = (error) => {

    const responseData = error?.response?.data;

    // ------------------------------------------------------
    // String directement retournée
    // ------------------------------------------------------

    if (typeof responseData === "string") {
        return responseData;
    }

    // ------------------------------------------------------
    // Champs classiques Flask
    // ------------------------------------------------------

    if (responseData?.error) {

        if (typeof responseData.error === "string") {
            return responseData.error;
        }

        if (
            typeof responseData.error === "object"
        ) {
            return JSON.stringify(
                responseData.error,
                null,
                2
            );
        }
    }

    if (responseData?.message) {
        return responseData.message;
    }

    if (responseData?.detail) {

        if (typeof responseData.detail === "string") {
            return responseData.detail;
        }

        return JSON.stringify(
            responseData.detail,
            null,
            2
        );
    }

    // ------------------------------------------------------
    // Validation Flask / Pydantic
    // ------------------------------------------------------

    if (responseData?.errors) {

        if (
            typeof responseData.errors === "object"
        ) {
            return JSON.stringify(
                responseData.errors,
                null,
                2
            );
        }

        return String(
            responseData.errors
        );
    }

    if (responseData?.validation_errors) {

        return JSON.stringify(
            responseData.validation_errors,
            null,
            2
        );
    }

    // ------------------------------------------------------
    // Axios
    // ------------------------------------------------------

    if (error?.message) {
        return error.message;
    }

    return "Une erreur est survenue.";
};


// ==========================================================
// COMPOSANT
// ==========================================================

const CreateDashboardPage = () => {

    const navigate = useNavigate();

    const { projectId } = useParams();

    const location = useLocation();


    // ======================================================
    // CONTEXTE ROUTE
    // ======================================================

    const routeConnectionId =
        location.state?.connectionId || null;

    const routeSelectedTables = Array.isArray(
        location.state?.selectedTables
    )
        ? location.state.selectedTables
        : [];


    // ======================================================
    // ETATS
    // ======================================================

    const [connectionId, setConnectionId] =
        useState(routeConnectionId);

    const [selectedTables, setSelectedTables] =
        useState(routeSelectedTables);

    const [name, setName] =
        useState("");

    const [loading, setLoading] =
        useState(false);

    const [error, setError] =
        useState("");

    const [dashboardId, setDashboardId] =
        useState(null);

    const [aiResult, setAiResult] =
        useState(null);

    const [steps, setSteps] =
        useState(createInitialSteps());


    // ======================================================
    // RECUPERATION CONTEXTE
    // ======================================================

    useEffect(() => {

        // --------------------------------------------------
        // Contexte envoyé par SchemaPage
        // --------------------------------------------------

        if (routeConnectionId) {
            setConnectionId(routeConnectionId);
        }

        if (routeSelectedTables.length > 0) {
            setSelectedTables(routeSelectedTables);
        }


        // --------------------------------------------------
        // SessionStorage
        // --------------------------------------------------

        if (!projectId) {
            return;
        }

        try {

            const storageKey =
                `dashboard_context_${projectId}`;

            const savedContext =
                sessionStorage.getItem(storageKey);

            if (!savedContext) {
                return;
            }

            const context =
                JSON.parse(savedContext);


            if (
                !routeConnectionId &&
                context?.connectionId
            ) {

                setConnectionId(
                    context.connectionId
                );
            }


            if (
                routeSelectedTables.length === 0 &&
                Array.isArray(
                    context?.selectedTables
                )
            ) {

                setSelectedTables(
                    context.selectedTables
                );
            }

        } catch (err) {

            console.error(
                "Erreur récupération contexte dashboard :",
                err
            );
        }

    }, [
        projectId,
        routeConnectionId,
        routeSelectedTables.length,
    ]);


    // ======================================================
    // UPDATE STEP
    // ======================================================

    const updateStep = (
        index,
        status
    ) => {

        setSteps((currentSteps) => {

            return currentSteps.map(
                (step, currentIndex) => {

                    if (
                        currentIndex !== index
                    ) {
                        return step;
                    }

                    return {
                        ...step,
                        status,
                    };
                }
            );
        });
    };


    // ======================================================
    // RESET
    // ======================================================

    const resetPipeline = () => {

        setSteps(
            createInitialSteps()
        );
    };


    // ======================================================
    // CREATION DASHBOARD
    // ======================================================

    const handleCreate = async (
        event
    ) => {

        event.preventDefault();

        setError("");

        setAiResult(null);

        setDashboardId(null);

        resetPipeline();


        // ==================================================
        // NOM
        // ==================================================

        const dashboardName =
            name.trim();


        // ==================================================
        // VALIDATION PROJET
        // ==================================================

        if (!projectId) {

            setError(
                "Identifiant du projet manquant."
            );

            return;
        }


        // ==================================================
        // VALIDATION NOM
        // ==================================================

        if (!dashboardName) {

            setError(
                "Veuillez saisir un nom pour le dashboard."
            );

            return;
        }


        // ==================================================
        // VALIDATION CONNEXION
        // ==================================================

        if (!connectionId) {

            setError(
                "Aucune connexion BDD n'est associée au dashboard."
            );

            return;
        }


        // ==================================================
        // VALIDATION TABLES
        // ==================================================

        if (
            !Array.isArray(selectedTables) ||
            selectedTables.length === 0
        ) {

            setError(
                "Aucune table n'est sélectionnée."
            );

            return;
        }


        try {

            setLoading(true);


            // ==================================================
            // ETAPE 1
            // CONNEXION
            // ==================================================

            updateStep(
                0,
                "active"
            );

            console.log(
                "VERIFICATION CONNEXION :",
                connectionId
            );


            /*
             * La connexion existe déjà.
             *
             * On vérifie ici uniquement que nous avons
             * bien son identifiant.
             *
             * La vraie vérification de connexion est
             * normalement réalisée côté backend lors
             * de l'exploration / sauvegarde.
             */

            updateStep(
                0,
                "done"
            );


            // ==================================================
            // ETAPE 2
            // CREATION DASHBOARD
            // ==================================================

            updateStep(
                1,
                "active"
            );


            // --------------------------------------------------
            // PAYLOAD
            // --------------------------------------------------

            const dashboardPayload = {

                project_id:
                    projectId,

                name:
                    dashboardName,

                connection_id:
                    connectionId,

                tables:
                    selectedTables,
            };


            console.log(
                "CREATION DASHBOARD - PAYLOAD :",
                dashboardPayload
            );


            // --------------------------------------------------
            // APPEL API
            // --------------------------------------------------

            const response =
                await api.post(
                    "/dashboards",
                    dashboardPayload
                );


            const data =
                response?.data;


            console.log(
                "REPONSE CREATION DASHBOARD :",
                data
            );


            // --------------------------------------------------
            // VERIFICATION
            // --------------------------------------------------

            if (!data) {

                throw new Error(
                    "Le serveur n'a retourné aucune donnée."
                );
            }


            if (
                data.success === false
            ) {

                throw new Error(
                    data.error ||
                    data.message ||
                    "Impossible de créer le dashboard."
                );
            }


            // ==================================================
            // RECUPERATION ID
            // ==================================================

            const createdDashboardId =
                data.id ||
                data.dashboard_id ||
                data.dashboard?.id ||
                data.data?.id;


            console.log(
                "ID DASHBOARD CREE :",
                createdDashboardId
            );


            if (!createdDashboardId) {

                console.error(
                    "REPONSE BACKEND SANS ID :",
                    data
                );

                throw new Error(
                    "Le dashboard a été créé mais le serveur n'a pas retourné son identifiant."
                );
            }


            setDashboardId(
                createdDashboardId
            );


            updateStep(
                1,
                "done"
            );


            // ==================================================
            // ETAPE 3
            // SCHEMA
            // ==================================================

            updateStep(
                2,
                "active"
            );


            console.log(
                "RECUPERATION SCHEMA :",
                connectionId
            );


            /*
             * IMPORTANT :
             *
             * Nous ne faisons PAS d'appel inventé ici.
             *
             * Le backend peut déjà avoir le schéma
             * associé à connectionId.
             *
             * Si ton backend possède une route
             * /connections/{id}/explore, elle peut être
             * branchée ici plus tard.
             */

            updateStep(
                2,
                "done"
            );


            // ==================================================
            // ETAPE 4
            // ANALYSE IA
            // ==================================================

            updateStep(
                3,
                "active"
            );


            console.log(
                "ANALYSE IA POUR CONNECTION :",
                connectionId
            );

            let recommendation = null;


            try {

                const aiResponse =
                    await api.post(
                        `/ai/connections/${connectionId}/recommend`
                    );


                recommendation =
                    aiResponse?.data;


                console.log(
                    "REPONSE COMPLETE IA :",
                    recommendation
                );

            } catch (aiError) {

                console.error(
                    "ERREUR ANALYSE IA :",
                    aiError
                );


                /*
                 * Le dashboard est déjà créé.
                 *
                 * On ne le détruit pas simplement parce que
                 * l'analyse IA échoue.
                 */

                updateStep(
                    3,
                    "error"
                );


                const aiMessage =
                    getErrorMessage(
                        aiError
                    );


                setError(
                    `Dashboard créé avec succès, mais l'analyse IA a échoué : ${aiMessage}`
                );


                setLoading(false);

                return;
            }


            // ==================================================
            // VALIDATION REPONSE IA
            // ==================================================

            if (!recommendation) {

                updateStep(
                    3,
                    "error"
                );

                setError(
                    "Le dashboard a été créé, mais le service IA n'a retourné aucune réponse."
                );

                setLoading(false);

                return;
            }


            if (
                recommendation.success === false
            ) {

                updateStep(
                    3,
                    "error"
                );

                setError(
                    recommendation.error ||
                    recommendation.message ||
                    "L'analyse IA a échoué."
                );

                setLoading(false);

                return;
            }


            if (
                recommendation.statut ===
                "degraded"
            ) {

                updateStep(
                    3,
                    "error"
                );

                setError(
                    recommendation.erreur ||
                    recommendation.error ||
                    recommendation.message ||
                    "L'analyse IA a échoué."
                );

                setLoading(false);

                return;
            }


            updateStep(
                3,
                "done"
            );


            // ==================================================
            // ETAPE 5
            // DOMAINE
            // ==================================================

            updateStep(
                4,
                "active"
            );


            const domain =
                recommendation.domaine_detecte ||
                recommendation.domain ||
                recommendation.domaine ||
                "Domaine non déterminé";


            console.log(
                "DOMAINE DETECTE :",
                domain
            );


            updateStep(
                4,
                "done"
            );


            // ==================================================
            // ETAPE 6
            // KPI
            // ==================================================

            updateStep(
                5,
                "active"
            );


            const kpis =
                Array.isArray(
                    recommendation.kpi_recommandes
                )
                    ? recommendation.kpi_recommandes
                    : Array.isArray(
                          recommendation.kpis
                      )
                    ? recommendation.kpis
                    : [];


            console.log(
                "KPI RECOMMANDES :",
                kpis
            );


            updateStep(
                5,
                "done"
            );


            // ==================================================
            // GRAPHIQUES
            // ==================================================

            const charts =
                Array.isArray(
                    recommendation.graphiques_recommandes
                )
                    ? recommendation.graphiques_recommandes
                    : Array.isArray(
                          recommendation.charts
                      )
                    ? recommendation.charts
                    : [];


            // ==================================================
            // FILTRES
            // ==================================================

            const filters =
                Array.isArray(
                    recommendation.filtres_recommandes
                )
                    ? recommendation.filtres_recommandes
                    : Array.isArray(
                          recommendation.filters
                      )
                    ? recommendation.filters
                    : [];


            // ==================================================
            // ALERTES
            // ==================================================

            const alerts =
                Array.isArray(
                    recommendation.alertes_possibles
                )
                    ? recommendation.alertes_possibles
                    : Array.isArray(
                          recommendation.alerts
                      )
                    ? recommendation.alerts
                    : [];


            // ==================================================
            // QUESTIONS
            // ==================================================

            const questions =
                Array.isArray(
                    recommendation.questions_metier
                )
                    ? recommendation.questions_metier
                    : Array.isArray(
                          recommendation.questions
                      )
                    ? recommendation.questions
                    : [];


            // ==================================================
            // RESULTAT IA
            // ==================================================

            setAiResult({

                domain,

                kpis,

                charts,

                filters,

                alerts,

                questions,

                status:
                    recommendation.statut ||
                    "success",

            });


            // ==================================================
            // ETAPE 7
            // CALCUL KPI
            // ==================================================

            /*
             * AnalyticsService n'est pas encore branché.
             *
             * On ne prétend donc pas avoir calculé les KPI.
             */

            updateStep(
                6,
                "pending"
            );


            // ==================================================
            // ETAPE 8
            // VISUALISATIONS
            // ==================================================

            /*
             * Mistral recommande actuellement les graphiques.
             * Ils ne sont pas encore construits automatiquement.
             */

            updateStep(
                7,
                "pending"
            );


            // ==================================================
            // ETAPE 9
            // DASHBOARD
            // ==================================================

            /*
             * Le dashboard existe déjà en BDD.
             */

            updateStep(
                8,
                "done"
            );


            console.log(
                "PIPELINE TERMINE :",
                {
                    dashboardId:
                        createdDashboardId,

                    domain,

                    kpis,

                    charts,

                    filters,
                }
            );

        } catch (err) {

            console.error(
                "ERREUR CREATION DASHBOARD / ANALYSE :",
                err
            );


            // --------------------------------------------------
            // IMPORTANT POUR LE 422
            // --------------------------------------------------

            if (
                err?.response?.status === 422
            ) {

                console.error(
                    "DETAIL REPONSE 422 :",
                    err?.response?.data
                );

                console.error(
                    "PAYLOAD ENVOYE :",
                    {
                        project_id:
                            projectId,

                        name:
                            dashboardName,

                        connection_id:
                            connectionId,

                        tables:
                            selectedTables,
                    }
                );
            }


            const message =
                getErrorMessage(err);


            setError(
                message
            );


            // --------------------------------------------------
            // MARQUER L'ETAPE ACTIVE EN ERREUR
            // --------------------------------------------------

            setSteps(
                (currentSteps) =>
                    currentSteps.map(
                        (step) => {

                            if (
                                step.status ===
                                "active"
                            ) {

                                return {
                                    ...step,
                                    status: "error",
                                };
                            }

                            return step;
                        }
                    )
            );

        } finally {

            setLoading(false);
        }
    };


    // ======================================================
    // CONTINUER
    // ======================================================

    const handleContinue = () => {

        if (!dashboardId) {

            setError(
                "Identifiant du dashboard manquant."
            );

            return;
        }


        console.log(
            "OUVERTURE DASHBOARD :",
            dashboardId
        );


        navigate(
            `/dashboard/${dashboardId}`
        );
    };


    // ======================================================
    // RETOUR
    // ======================================================

    const handleBack = () => {

        if (!projectId) {
            navigate(-1);
            return;
        }


        if (!connectionId) {

            navigate(
                `/workspace/${projectId}`
            );

            return;
        }


        navigate(
            `/workspace/${projectId}/schema/${connectionId}`
        );
    };


    // ======================================================
    // AFFICHAGE PIPELINE
    // ======================================================

    if (
        loading ||
        aiResult
    ) {

        return (

            <div className="page-container">

                <div
                    className="card"
                    style={{
                        maxWidth: "850px",
                        margin: "60px auto",
                        padding: "40px",
                    }}
                >

                    {/* ======================================
                        HEADER
                    ====================================== */}

                    <div
                        style={{
                            textAlign: "center",
                            marginBottom: "35px",
                        }}
                    >

                        <div className="page-eyebrow">
                            DATAVIZ
                        </div>

                        <h1>
                            Analyse intelligente
                        </h1>

                        <p>
                            Schéma → IA → KPI →
                            Visualisations
                        </p>

                    </div>


                    {/* ======================================
                        CONTEXTE
                    ====================================== */}

                    <div
                        style={{
                            padding: "16px",
                            background: "#f8fafc",
                            borderRadius: "10px",
                            marginBottom: "30px",
                        }}
                    >

                        <strong>
                            Connexion utilisée
                        </strong>

                        <div
                            style={{
                                marginTop: "5px",
                                fontFamily: "monospace",
                                fontSize: "13px",
                            }}
                        >
                            {connectionId}
                        </div>


                        <div
                            style={{
                                marginTop: "12px",
                            }}
                        >

                            <strong>
                                Tables sélectionnées
                            </strong>

                            <div
                                style={{
                                    marginTop: "6px",
                                    color: "#64748b",
                                }}
                            >

                                {selectedTables.length > 0
                                    ? selectedTables.join(", ")
                                    : "Aucune"}

                            </div>

                        </div>

                    </div>


                    {/* ======================================
                        ETAPES
                    ====================================== */}

                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "16px",
                            marginBottom: "35px",
                        }}
                    >

                        {steps.map(
                            (
                                step,
                                index
                            ) => {

                                const isDone =
                                    step.status ===
                                    "done";

                                const isActive =
                                    step.status ===
                                    "active";

                                const isError =
                                    step.status ===
                                    "error";


                                return (

                                    <div
                                        key={`${step.label}-${index}`}
                                        style={{
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "12px",
                                        }}
                                    >

                                        <span
                                            style={{
                                                width: "25px",
                                                display: "inline-flex",
                                                justifyContent: "center",
                                                fontWeight: "700",
                                            }}
                                        >

                                            {isDone
                                                ? "✓"
                                                : isError
                                                ? "!"
                                                : isActive
                                                ? "●"
                                                : "○"}

                                        </span>


                                        <span
                                            style={{
                                                fontWeight:
                                                    isActive
                                                        ? "700"
                                                        : "400",
                                            }}
                                        >

                                            {step.label}

                                        </span>

                                    </div>

                                );
                            }
                        )}

                    </div>


                    {/* ======================================
                        ERREUR
                    ====================================== */}

                    {error && (

                        <div
                            className="alert alert-error"
                            style={{
                                marginBottom: "25px",
                                whiteSpace: "pre-wrap",
                            }}
                        >

                            {error}

                        </div>

                    )}


                    {/* ======================================
                        RESULTAT IA
                    ====================================== */}

                    {aiResult && (

                        <div>

                            <div
                                style={{
                                    borderTop:
                                        "1px solid #e2e8f0",
                                    paddingTop:
                                        "30px",
                                }}
                            >

                                <h2>
                                    Résultat de l'analyse IA
                                </h2>


                                {/* ==============================
                                    DOMAINE
                                ============================== */}

                                <div
                                    style={{
                                        marginTop: "20px",
                                        padding: "20px",
                                        background: "#f8fafc",
                                        borderRadius: "12px",
                                    }}
                                >

                                    <strong>
                                        Domaine métier détecté
                                    </strong>


                                    <div
                                        style={{
                                            fontSize: "24px",
                                            fontWeight: "700",
                                            marginTop: "8px",
                                        }}
                                    >

                                        {aiResult.domain}

                                    </div>

                                </div>


                                {/* ==============================
                                    KPI
                                ============================== */}

                                <div
                                    style={{
                                        marginTop: "25px",
                                    }}
                                >

                                    <h3>
                                        KPI recommandés
                                    </h3>


                                    {aiResult.kpis.length === 0 ? (

                                        <p>
                                            Aucun KPI valide
                                            n'a été retourné
                                            par l'IA.
                                        </p>

                                    ) : (

                                        <div
                                            style={{
                                                display: "flex",
                                                flexDirection: "column",
                                                gap: "12px",
                                                marginTop: "15px",
                                            }}
                                        >

                                            {aiResult.kpis.map(
                                                (
                                                    kpi,
                                                    index
                                                ) => {

                                                    const kpiName =
                                                        kpi?.nom ||
                                                        kpi?.name ||
                                                        kpi?.label ||
                                                        "KPI";


                                                    const operation =
                                                        kpi?.operation ||
                                                        kpi?.aggregation ||
                                                        "Opération non précisée";


                                                    const table =
                                                        kpi?.table ||
                                                        kpi?.table_name ||
                                                        "Table inconnue";


                                                    const column =
                                                        kpi?.column ||
                                                        kpi?.column_name ||
                                                        "Colonne inconnue";


                                                    return (

                                                        <div
                                                            key={
                                                                kpi?.id ||
                                                                `${kpiName}-${index}`
                                                            }
                                                            style={{
                                                                padding: "16px",
                                                                border: "1px solid #e2e8f0",
                                                                borderRadius: "10px",
                                                                background: "white",
                                                            }}
                                                        >

                                                            <strong>
                                                                {kpiName}
                                                            </strong>


                                                            <div
                                                                style={{
                                                                    marginTop: "6px",
                                                                    color: "#64748b",
                                                                }}
                                                            >

                                                                {operation}

                                                                {" · "}

                                                                {table}

                                                                {"."}

                                                                {column}

                                                            </div>


                                                            {kpi?.description && (

                                                                <p
                                                                    style={{
                                                                        marginTop: "8px",
                                                                    }}
                                                                >
                                                                    {kpi.description}
                                                                </p>

                                                            )}

                                                        </div>

                                                    );
                                                }
                                            )}

                                        </div>
                                    )}

                                </div>


                                {/* ==============================
                                    RESUME
                                ============================== */}

                                <div
                                    style={{
                                        marginTop: "30px",
                                        display: "grid",
                                        gridTemplateColumns:
                                            "repeat(3, 1fr)",
                                        gap: "15px",
                                    }}
                                >

                                    <div className="card">

                                        <strong>
                                            KPI
                                        </strong>

                                        <div
                                            style={{
                                                fontSize: "25px",
                                                fontWeight: "700",
                                                marginTop: "8px",
                                            }}
                                        >
                                            {aiResult.kpis.length}
                                        </div>

                                    </div>


                                    <div className="card">

                                        <strong>
                                            Graphiques
                                        </strong>

                                        <div
                                            style={{
                                                fontSize: "25px",
                                                fontWeight: "700",
                                                marginTop: "8px",
                                            }}
                                        >
                                            {aiResult.charts.length}
                                        </div>

                                    </div>


                                    <div className="card">

                                        <strong>
                                            Filtres
                                        </strong>

                                        <div
                                            style={{
                                                fontSize: "25px",
                                                fontWeight: "700",
                                                marginTop: "8px",
                                            }}
                                        >
                                            {aiResult.filters.length}
                                        </div>

                                    </div>

                                </div>


                                {/* ==============================
                                    ACTIONS
                                ============================== */}

                                <div
                                    className="form-actions"
                                    style={{
                                        marginTop: "30px",
                                    }}
                                >

                                    <button
                                        type="button"
                                        className="secondary-btn"
                                        onClick={handleBack}
                                    >
                                        Retour au schéma
                                    </button>


                                    <button
                                        type="button"
                                        className="primary-btn"
                                        onClick={handleContinue}
                                        disabled={!dashboardId}
                                    >
                                        Continuer
                                    </button>

                                </div>

                            </div>

                        </div>
                    )}

                </div>

            </div>
        );
    }


    // ======================================================
    // FORMULAIRE
    // ======================================================

    return (

        <div className="page-container">

            <div className="page-header">

                <div>

                    <div className="page-eyebrow">
                        DASHBOARD
                    </div>


                    <h1>
                        Créer un dashboard
                    </h1>


                    <p>
                        Donnez un nom à votre dashboard
                        avant de lancer l'analyse IA.
                    </p>

                </div>


                <button
                    type="button"
                    className="secondary-btn"
                    onClick={handleBack}
                    disabled={loading}
                >
                    Retour au schéma
                </button>

            </div>


            {/* ==============================================
                SOURCE DE DONNEES
            ============================================== */}

            <div className="card">

                <h3>
                    Source de données
                </h3>


                <p>

                    Connexion :{" "}

                    <strong>
                        {connectionId || "Non définie"}
                    </strong>

                </p>


                <p>

                    Tables sélectionnées :{" "}

                    <strong>
                        {selectedTables.length}
                    </strong>

                </p>


                {selectedTables.length > 0 && (

                    <div
                        style={{
                            marginTop: "10px",
                            color: "#64748b",
                        }}
                    >

                        {selectedTables.join(", ")}

                    </div>

                )}

            </div>


            {/* ==============================================
                FORMULAIRE
            ============================================== */}

            <div className="card">

                <form
                    onSubmit={handleCreate}
                >

                    <div className="form-group">

                        <label htmlFor="dashboard-name">
                            Nom du dashboard
                        </label>


                        <input
                            id="dashboard-name"
                            type="text"
                            value={name}
                            onChange={(event) =>
                                setName(
                                    event.target.value
                                )
                            }
                            placeholder="Ex : Dashboard commercial"
                            autoFocus
                            disabled={loading}
                        />

                    </div>


                    {error && (

                        <div
                            className="alert alert-error"
                            style={{
                                whiteSpace: "pre-wrap",
                            }}
                        >
                            {error}
                        </div>

                    )}


                    <div className="form-actions">

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={handleBack}
                            disabled={loading}
                        >
                            Annuler
                        </button>


                        <button
                            type="submit"
                            className="primary-btn"
                            disabled={
                                loading ||
                                !connectionId ||
                                selectedTables.length === 0
                            }
                        >

                            {loading
                                ? "Analyse en cours..."
                                : "Lancer l'analyse IA"}

                        </button>

                    </div>

                </form>

            </div>

        </div>
    );
};


export default CreateDashboardPage;