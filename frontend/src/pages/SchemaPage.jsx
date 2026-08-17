// src/pages/SchemaPage.jsx

import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { connectionsApi } from "../api/connections";

const SchemaPage = () => {
    const { projectId, connectionId } = useParams();
    const navigate = useNavigate();

    // ==========================================================
    // ETATS
    // ==========================================================

    const [schema, setSchema] = useState(null);

    const [loading, setLoading] = useState(true);

    const [exploring, setExploring] = useState(false);

    const [savingTables, setSavingTables] = useState(false);

    const [error, setError] = useState("");

    const [message, setMessage] = useState("");

    const [selectedTables, setSelectedTables] = useState([]);


    // ==========================================================
    // NORMALISER LE SCHEMA
    // ==========================================================

    const normalizeSchema = (data) => {
        if (!data) {
            return null;
        }

        /*
         * Backend possible :
         *
         * {
         *     success: true,
         *     schema: {
         *         tables: [...]
         *     }
         * }
         */

        if (data.schema) {
            return data.schema;
        }

        /*
         * Ou directement :
         *
         * {
         *     tables: [...]
         * }
         */

        return data;
    };


    // ==========================================================
    // EXTRAIRE LES TABLES
    // ==========================================================

    const getTables = (schemaData) => {
        if (!schemaData) {
            return [];
        }

        const rawTables =
            schemaData.tables ||
            schemaData.tables_info ||
            schemaData.tables_schema ||
            [];

        if (!Array.isArray(rawTables)) {
            return [];
        }

        return rawTables.map((table, index) => {
            const name =
                table?.name ||
                table?.table_name ||
                table?.nom ||
                `Table ${index + 1}`;

            const columns =
                Array.isArray(table?.columns)
                    ? table.columns
                    : Array.isArray(table?.colonnes)
                    ? table.colonnes
                    : [];

            return {
                name,
                columns,
            };
        });
    };


    // ==========================================================
    // CHARGER LE SCHEMA EXISTANT
    // ==========================================================

    const loadSchema = async () => {
        if (!connectionId) {
            setError(
                "Identifiant de connexion manquant."
            );

            return null;
        }

        try {
            setLoading(true);
            setError("");
            setMessage("Chargement du schéma...");

            console.log(
                "CHARGEMENT SCHEMA - CONNECTION ID :",
                connectionId
            );

            const response =
                await connectionsApi.schema(
                    connectionId
                );

            console.log(
                "REPONSE SCHEMA :",
                response.data
            );

            if (
                !response.data ||
                response.data.success === false
            ) {
                throw new Error(
                    response.data?.error ||
                    response.data?.message ||
                    "Impossible de charger le schéma."
                );
            }

            const realSchema =
                normalizeSchema(
                    response.data
                );

            if (!realSchema) {
                return null;
            }

            const tables =
                getTables(realSchema);

            /*
             * Aucun tableau = schéma non exploitable.
             * Dans ce cas, on lancera l'exploration réelle.
             */

            if (tables.length === 0) {
                return null;
            }

            console.log(
                "SCHEMA CACHE VALIDE :",
                realSchema
            );

            console.log(
                "TABLES DU CACHE :",
                tables
            );

            setSchema(realSchema);

            /*
             * Récupération d'une éventuelle sélection
             * déjà enregistrée côté backend.
             */

            const backendSelectedTables =
                response.data?.selected_tables ||
                realSchema?.selected_tables ||
                [];

            if (
                Array.isArray(
                    backendSelectedTables
                )
            ) {
                setSelectedTables(
                    backendSelectedTables
                );
            } else {
                setSelectedTables([]);
            }

            setMessage(
                `${tables.length} table${
                    tables.length !== 1
                        ? "s"
                        : ""
                } disponible${
                    tables.length !== 1
                        ? "s"
                        : ""
                }.`
            );

            return realSchema;

        } catch (err) {
            /*
             * Une erreur lors du chargement du cache
             * ne bloque pas l'exploration réelle.
             */

            console.log(
                "Aucun schéma disponible en cache.",
                err
            );

            return null;

        } finally {
            setLoading(false);
        }
    };


    // ==========================================================
    // EXPLORER REELLEMENT LA BASE
    // ==========================================================

    const exploreDatabase = async () => {
        if (!connectionId) {
            setError(
                "Identifiant de connexion manquant."
            );

            return null;
        }

        try {
            setExploring(true);

            setError("");

            setMessage(
                "Exploration réelle de la base de données..."
            );

            console.log(
                "EXPLORATION CONNECTION ID :",
                connectionId
            );

            const response =
                await connectionsApi.explore(
                    connectionId
                );

            console.log(
                "REPONSE EXPLORATION :",
                response.data
            );

            if (
                !response.data ||
                response.data.success === false
            ) {
                throw new Error(
                    response.data?.error ||
                    response.data?.message ||
                    "Impossible d'explorer la base de données."
                );
            }

            const realSchema =
                normalizeSchema(
                    response.data
                );

            if (!realSchema) {
                throw new Error(
                    "Le serveur n'a retourné aucun schéma."
                );
            }

            const tables =
                getTables(realSchema);

            console.log(
                "SCHEMA FINAL :",
                realSchema
            );

            console.log(
                "TABLES DETECTEES :",
                tables
            );

            setSchema(realSchema);

            /*
             * Une nouvelle exploration signifie
             * qu'on repart sans sélection.
             */

            setSelectedTables([]);

            setMessage(
                `Exploration terminée : ${tables.length} table${
                    tables.length !== 1
                        ? "s"
                        : ""
                } détectée${
                    tables.length !== 1
                        ? "s"
                        : ""
                }.`
            );

            return realSchema;

        } catch (err) {
            console.error(
                "ERREUR EXPLORATION SCHEMA :",
                err
            );

            const errorMessage =
                err.response?.data?.error ||
                err.response?.data?.message ||
                err.message ||
                "Impossible d'explorer la base de données.";

            setError(
                errorMessage
            );

            return null;

        } finally {
            setExploring(false);
        }
    };


    // ==========================================================
    // INITIALISATION
    // ==========================================================

    useEffect(() => {
        let cancelled = false;

        const initialize = async () => {
            if (!projectId) {
                setError(
                    "Identifiant du projet manquant."
                );

                setLoading(false);

                return;
            }

            if (!connectionId) {
                setError(
                    "Identifiant de connexion manquant."
                );

                setLoading(false);

                return;
            }

            setLoading(true);

            setError("");

            /*
             * 1. Chercher d'abord un schéma existant.
             */

            const cachedSchema =
                await loadSchema();

            if (cancelled) {
                return;
            }

            /*
             * 2. Si aucun schéma valide n'existe,
             *    explorer réellement la base.
             */

            if (!cachedSchema) {
                await exploreDatabase();
            }

            if (cancelled) {
                return;
            }

            setLoading(false);
        };

        initialize();

        return () => {
            cancelled = true;
        };

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectId, connectionId]);


    // ==========================================================
    // TABLES
    // ==========================================================

    const tables =
        getTables(schema);


    // ==========================================================
    // SELECTIONNER / DESELECTIONNER UNE TABLE
    // ==========================================================

    const toggleTable = (tableName) => {
        setSelectedTables((current) => {
            if (
                current.includes(tableName)
            ) {
                return current.filter(
                    (name) =>
                        name !== tableName
                );
            }

            return [
                ...current,
                tableName,
            ];
        });

        setMessage("");

        setError("");
    };


    // ==========================================================
    // TOUT SELECTIONNER
    // ==========================================================

    const selectAllTables = () => {
        setSelectedTables(
            tables.map(
                (table) =>
                    table.name
            )
        );

        setMessage("");

        setError("");
    };


    // ==========================================================
    // TOUT DESELECTIONNER
    // ==========================================================

    const deselectAllTables = () => {
        setSelectedTables([]);

        setMessage("");

        setError("");
    };


    // ==========================================================
    // ENREGISTRER LES TABLES
    // ==========================================================

    const saveTables = async () => {
        if (!connectionId) {
            setError(
                "Identifiant de connexion manquant."
            );

            return false;
        }

        if (
            selectedTables.length === 0
        ) {
            setError(
                "Veuillez sélectionner au moins une table."
            );

            return false;
        }

        try {
            setSavingTables(true);

            setError("");

            setMessage(
                "Enregistrement des tables sélectionnées..."
            );

            console.log(
                "TABLES A ENREGISTRER :",
                selectedTables
            );

            const response =
                await connectionsApi.saveTables(
                    connectionId,
                    {
                        tables:
                            selectedTables,
                    }
                );

            console.log(
                "REPONSE SAVE TABLES :",
                response.data
            );

            if (
                !response.data ||
                response.data.success === false
            ) {
                throw new Error(
                    response.data?.error ||
                    response.data?.message ||
                    "Impossible d'enregistrer les tables."
                );
            }

            setMessage(
                `${selectedTables.length} table${
                    selectedTables.length !== 1
                        ? "s"
                        : ""
                } sélectionnée${
                    selectedTables.length !== 1
                        ? "s"
                        : ""
                } avec succès.`
            );

            return true;

        } catch (err) {
            console.error(
                "ERREUR SAUVEGARDE TABLES :",
                err
            );

            setError(
                err.response?.data?.error ||
                err.response?.data?.message ||
                err.message ||
                "Impossible d'enregistrer les tables."
            );

            return false;

        } finally {
            setSavingTables(false);
        }
    };


    // ==========================================================
    // CREER LE DASHBOARD
    // ==========================================================

    const createDashboard = async () => {
        /*
         * Cette fonction était absente dans ton fichier.
         *
         * CreateDashboardPage.jsx attend :
         *
         * location.state.connectionId
         * location.state.selectedTables
         *
         * On doit donc :
         *
         * 1. vérifier les IDs ;
         * 2. vérifier la sélection ;
         * 3. sauvegarder les tables ;
         * 4. naviguer vers CreateDashboardPage ;
         * 5. transmettre connectionId + selectedTables.
         */

        if (!projectId) {
            setError(
                "Identifiant du projet manquant."
            );

            return;
        }

        if (!connectionId) {
            setError(
                "Identifiant de connexion manquant."
            );

            return;
        }

        if (
            selectedTables.length === 0
        ) {
            setError(
                "Sélectionnez au moins une table avant de créer le dashboard."
            );

            return;
        }

        try {
            setSavingTables(true);

            setError("");

            setMessage(
                "Enregistrement des tables avant la création du dashboard..."
            );

            console.log(
                "PREPARATION DASHBOARD :",
                {
                    projectId,
                    connectionId,
                    selectedTables,
                }
            );

            /*
             * Sauvegarde obligatoire côté backend.
             */

            const response =
                await connectionsApi.saveTables(
                    connectionId,
                    {
                        tables:
                            selectedTables,
                    }
                );

            console.log(
                "TABLES SAUVEGARDEES AVANT DASHBOARD :",
                response.data
            );

            if (
                !response.data ||
                response.data.success === false
            ) {
                throw new Error(
                    response.data?.error ||
                    response.data?.message ||
                    "Impossible d'enregistrer les tables."
                );
            }

            /*
             * Navigation vers :
             *
             * /workspace/:projectId/dashboards/create
             *
             * CreateDashboardPage récupérera :
             *
             * location.state.connectionId
             * location.state.selectedTables
             */

            const destination =
                `/workspace/${projectId}/dashboards/create`;

            console.log(
                "REDIRECTION CREATE DASHBOARD :",
                destination
            );

            navigate(
                destination,
                {
                    state: {
                        connectionId,
                        selectedTables: [
                            ...selectedTables,
                        ],
                    },
                }
            );

        } catch (err) {
            console.error(
                "ERREUR PREPARATION DASHBOARD :",
                err
            );

            const errorMessage =
                err.response?.data?.error ||
                err.response?.data?.message ||
                err.message ||
                "Impossible de préparer le dashboard.";

            setError(
                errorMessage
            );

        } finally {
            setSavingTables(false);
        }
    };


    // ==========================================================
    // REEXPLORER
    // ==========================================================

    const handleReexplore = async () => {
        setSchema(null);

        setSelectedTables([]);

        setError("");

        setMessage("");

        await exploreDatabase();
    };


    // ==========================================================
    // RETOUR
    // ==========================================================

    const handleBack = () => {
        /*
         * On revient dans le workspace du projet.
         *
         * C'est plus cohérent avec la route :
         *
         * /workspace/:projectId/...
         */

        if (projectId) {
            navigate(
                `/workspace/${projectId}`
            );
            return;
        }

        navigate(-1);
    };


    // ==========================================================
    // LOADING
    // ==========================================================

    if (
        loading ||
        exploring
    ) {
        return (
            <div className="page-container">

                <div className="card">

                    <h2>
                        Exploration du schéma
                    </h2>

                    <p>
                        {exploring
                            ? "Analyse réelle de la base de données en cours..."
                            : "Chargement du schéma..."
                        }
                    </p>

                    <div
                        className="loading-spinner"
                        style={{
                            marginTop:
                                "20px",
                        }}
                    />

                </div>

            </div>
        );
    }


    // ==========================================================
    // ERREUR SANS SCHEMA
    // ==========================================================

    if (
        error &&
        !schema
    ) {
        return (
            <div className="page-container">

                <div className="card">

                    <h2>
                        Impossible d'explorer la base
                    </h2>

                    <p className="status-error">
                        {error}
                    </p>

                    <div className="buttons-row">

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={handleBack}
                        >
                            Retour
                        </button>

                        <button
                            type="button"
                            className="primary-btn"
                            onClick={
                                handleReexplore
                            }
                            disabled={
                                exploring
                            }
                        >
                            {exploring
                                ? "Exploration..."
                                : "Réessayer l'exploration"
                            }
                        </button>

                    </div>

                </div>

            </div>
        );
    }


    // ==========================================================
    // RENDER
    // ==========================================================

    return (
        <div className="page-container schema-page">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header">

                <div>

                    <div className="page-eyebrow">
                        SOURCE DE DONNÉES
                    </div>

                    <h1>
                        Exploration du schéma
                    </h1>

                    <p>
                        Sélectionnez les tables qui serviront
                        à votre analyse et à votre dashboard.
                    </p>

                </div>

                <button
                    type="button"
                    className="secondary-btn"
                    onClick={handleBack}
                >
                    Retour au workspace
                </button>

            </div>


            {/* ==================================================
                MESSAGES
            ================================================== */}

            {(message || error) && (
                <div
                    className={
                        error
                            ? "status-message status-error"
                            : "status-message"
                    }
                >
                    {error || message}
                </div>
            )}


            {/* ==================================================
                INFORMATIONS CONNEXION
            ================================================== */}

            <div className="card">

                <div className="card-title">

                    <div>

                        <span className="card-kicker">
                            CONNEXION
                        </span>

                        <h2>
                            Source de données
                        </h2>

                    </div>

                </div>

                <p>
                    Connexion :
                    {" "}
                    <strong>
                        {connectionId}
                    </strong>
                </p>

                <p>
                    Projet :
                    {" "}
                    <strong>
                        {projectId}
                    </strong>
                </p>

            </div>


            {/* ==================================================
                SELECTION
            ================================================== */}

            {tables.length > 0 && (
                <div className="card">

                    <div className="card-title">

                        <div>

                            <span className="card-kicker">
                                SÉLECTION
                            </span>

                            <h2>
                                Tables disponibles
                            </h2>

                        </div>

                        <span className="count-badge">
                            {selectedTables.length}
                            {" / "}
                            {tables.length}
                        </span>

                    </div>

                    <div className="buttons-row">

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={
                                selectAllTables
                            }
                            disabled={
                                savingTables
                            }
                        >
                            Tout sélectionner
                        </button>

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={
                                deselectAllTables
                            }
                            disabled={
                                savingTables
                            }
                        >
                            Tout désélectionner
                        </button>

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={
                                handleReexplore
                            }
                            disabled={
                                exploring ||
                                savingTables
                            }
                        >
                            Actualiser le schéma
                        </button>

                    </div>

                </div>
            )}


            {/* ==================================================
                TABLES
            ================================================== */}

            <div className="card">

                <div className="card-title">

                    <div>

                        <span className="card-kicker">
                            STRUCTURE
                        </span>

                        <h2>
                            Tables à analyser
                        </h2>

                    </div>

                    <span>
                        {tables.length} table
                        {tables.length !== 1
                            ? "s"
                            : ""}
                    </span>

                </div>


                {tables.length === 0 ? (

                    <div className="empty-state">

                        <h3>
                            Aucune table trouvée
                        </h3>

                        <p>
                            La base de données ne contient
                            aucune table exploitable.
                        </p>

                        <button
                            type="button"
                            className="primary-btn"
                            onClick={
                                handleReexplore
                            }
                            disabled={
                                exploring
                            }
                        >
                            {exploring
                                ? "Exploration..."
                                : "Réexplorer la base"
                            }
                        </button>

                    </div>

                ) : (

                    <div className="schema-tables">

                        {tables.map(
                            (
                                table,
                                index
                            ) => {

                                const isSelected =
                                    selectedTables.includes(
                                        table.name
                                    );

                                return (
                                    <div
                                        className={`schema-table ${
                                            isSelected
                                                ? "selected"
                                                : ""
                                        }`}
                                        key={`${table.name}-${index}`}
                                    >

                                        {/* ==========================================
                                            HEADER TABLE
                                        ========================================== */}

                                        <div
                                            className="schema-table-header"
                                        >

                                            <div
                                                style={{
                                                    display:
                                                        "flex",
                                                    alignItems:
                                                        "center",
                                                    gap:
                                                        "15px",
                                                }}
                                            >

                                                <input
                                                    type="checkbox"
                                                    checked={
                                                        isSelected
                                                    }
                                                    onChange={() =>
                                                        toggleTable(
                                                            table.name
                                                        )
                                                    }
                                                    disabled={
                                                        savingTables
                                                    }
                                                />

                                                <div>

                                                    <h3>
                                                        {
                                                            table.name
                                                        }
                                                    </h3>

                                                    <span>
                                                        {
                                                            table
                                                                .columns
                                                                .length
                                                        }
                                                        {" "}
                                                        colonne
                                                        {
                                                            table
                                                                .columns
                                                                .length !==
                                                            1
                                                                ? "s"
                                                                : ""
                                                        }
                                                    </span>

                                                </div>

                                            </div>


                                            <button
                                                type="button"
                                                className={
                                                    isSelected
                                                        ? "primary-btn"
                                                        : "secondary-btn"
                                                }
                                                onClick={() =>
                                                    toggleTable(
                                                        table.name
                                                    )
                                                }
                                                disabled={
                                                    savingTables
                                                }
                                            >
                                                {isSelected
                                                    ? "Sélectionnée"
                                                    : "Sélectionner"
                                                }
                                            </button>

                                        </div>


                                        {/* ==========================================
                                            COLONNES
                                        ========================================== */}

                                        <div className="schema-columns">

                                            {table.columns.length ===
                                            0 ? (

                                                <p>
                                                    Aucune colonne détectée.
                                                </p>

                                            ) : (

                                                table.columns.map(
                                                    (
                                                        column,
                                                        columnIndex
                                                    ) => {

                                                        const columnName =
                                                            typeof column ===
                                                            "string"
                                                                ? column
                                                                : column?.name ||
                                                                  column?.column_name ||
                                                                  column?.nom ||
                                                                  `Colonne ${
                                                                      columnIndex +
                                                                      1
                                                                  }`;

                                                        const columnType =
                                                            typeof column ===
                                                            "string"
                                                                ? "Type inconnu"
                                                                : column?.type ||
                                                                  column?.data_type ||
                                                                  column?.column_type ||
                                                                  "Type inconnu";

                                                        return (
                                                            <div
                                                                className="schema-column"
                                                                key={`${columnName}-${columnIndex}`}
                                                            >

                                                                <strong>
                                                                    {
                                                                        columnName
                                                                    }
                                                                </strong>

                                                                <span>
                                                                    {
                                                                        columnType
                                                                    }
                                                                </span>

                                                            </div>
                                                        );
                                                    }
                                                )
                                            )}

                                        </div>

                                    </div>
                                );
                            }
                        )}

                    </div>
                )}

            </div>


            {/* ==================================================
                RESUME + ACTIONS
            ================================================== */}

            {tables.length > 0 && (
                <div className="card">

                    <h2>
                        Résumé
                    </h2>

                    <p>
                        Tables détectées :
                        {" "}
                        <strong>
                            {tables.length}
                        </strong>
                    </p>

                    <p>
                        Tables sélectionnées :
                        {" "}
                        <strong>
                            {selectedTables.length}
                        </strong>
                    </p>

                    <p>
                        Colonnes détectées :
                        {" "}
                        <strong>
                            {tables.reduce(
                                (
                                    total,
                                    table
                                ) =>
                                    total +
                                    table.columns.length,
                                0
                            )}
                        </strong>
                    </p>


                    <div className="buttons-row">

                        {/* ==========================================
                            ENREGISTRER
                        ========================================== */}

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={
                                saveTables
                            }
                            disabled={
                                savingTables ||
                                selectedTables.length ===
                                    0
                            }
                        >
                            {savingTables
                                ? "Enregistrement..."
                                : "Enregistrer les tables"
                            }
                        </button>


                        {/* ==========================================
                            CREER DASHBOARD
                        ========================================== */}

                        <button
                            type="button"
                            className="primary-btn"
                            onClick={
                                createDashboard
                            }
                            disabled={
                                savingTables ||
                                selectedTables.length ===
                                    0
                            }
                        >
                            {savingTables
                                ? "Préparation..."
                                : "Créer le dashboard"
                            }
                        </button>

                    </div>

                </div>
            )}


            {/* ==================================================
                SCHEMA BRUT
            ================================================== */}

            <div className="card">

                <details>

                    <summary>
                        Voir le schéma reçu
                    </summary>

                    <pre
                        style={{
                            overflowX:
                                "auto",
                            whiteSpace:
                                "pre-wrap",
                            wordBreak:
                                "break-word",
                            marginTop:
                                "15px",
                        }}
                    >
                        {JSON.stringify(
                            schema,
                            null,
                            2
                        )}
                    </pre>

                </details>

            </div>

        </div>
    );
};

export default SchemaPage;