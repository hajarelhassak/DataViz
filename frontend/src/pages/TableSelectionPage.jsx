// src/pages/TableSelectionPage.jsx

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { connectionsApi } from "../api/connections";

const TableSelectionPage = () => {
    const navigate = useNavigate();

    const {
        projectId,
        connectionId,
    } = useParams();

    // ==========================================================
    // ETATS
    // ==========================================================

    const [schema, setSchema] = useState(null);

    const [selectedTables, setSelectedTables] = useState([]);

    const [loading, setLoading] = useState(true);

    const [saving, setSaving] = useState(false);

    const [error, setError] = useState("");

    const [success, setSuccess] = useState("");

    // ==========================================================
    // RECUPERER LES TABLES DU SCHEMA
    // ==========================================================

    const tables = useMemo(() => {

        if (!schema) {
            return [];
        }

        const schemaTables =
            Array.isArray(schema.tables)
                ? schema.tables
                : [];

        return schemaTables
            .map((table, index) => {

                if (typeof table === "string") {
                    return {
                        name: table,
                        columns: [],
                    };
                }

                return {
                    name:
                        table?.name ||
                        table?.table_name ||
                        table?.nom ||
                        `Table ${index + 1}`,

                    columns:
                        Array.isArray(table?.columns)
                            ? table.columns
                            : Array.isArray(table?.colonnes)
                                ? table.colonnes
                                : [],
                };

            })
            .filter(
                (table) =>
                    table.name &&
                    table.name.trim()
            );

    }, [schema]);

    // ==========================================================
    // CHARGER LE SCHEMA
    // ==========================================================

    const loadSchema = async () => {

        if (!connectionId) {

            setError(
                "Identifiant de connexion manquant."
            );

            setLoading(false);

            return;
        }

        try {

            setLoading(true);

            setError("");

            setSuccess("");

            const response =
                await connectionsApi.schema(
                    connectionId
                );

            console.log(
                "SCHEMA POUR SELECTION :",
                response.data
            );

            const backendData =
                response.data;

            /*
             * Le backend peut retourner :
             *
             * {
             *     id: ...,
             *     connection_id: ...,
             *     schema: {
             *         tables: [...]
             *     }
             * }
             *
             * ou directement :
             *
             * {
             *     tables: [...]
             * }
             */

            const realSchema =
                backendData?.schema ||
                backendData;

            if (
                !realSchema ||
                !Array.isArray(
                    realSchema.tables
                )
            ) {

                throw new Error(
                    "Le schéma reçu ne contient aucune liste de tables valide."
                );

            }

            setSchema(realSchema);

        } catch (err) {

            console.error(
                "Erreur récupération schéma :",
                err
            );

            setError(
                err.response?.data?.error ||
                err.response?.data?.message ||
                err.message ||
                "Impossible de récupérer le schéma."
            );

        } finally {

            setLoading(false);

        }

    };

    // ==========================================================
    // INITIALISATION
    // ==========================================================

    useEffect(() => {

        loadSchema();

    }, [connectionId]);

    // ==========================================================
    // SELECTIONNER / DESELECTIONNER UNE TABLE
    // ==========================================================

    const toggleTable = (tableName) => {

        setSuccess("");

        setError("");

        setSelectedTables((previous) => {

            if (
                previous.includes(tableName)
            ) {

                return previous.filter(
                    (name) =>
                        name !== tableName
                );

            }

            return [
                ...previous,
                tableName,
            ];

        });

    };

    // ==========================================================
    // SELECTIONNER TOUTES LES TABLES
    // ==========================================================

    const selectAll = () => {

        setSuccess("");

        setError("");

        setSelectedTables(
            tables.map(
                (table) =>
                    table.name
            )
        );

    };

    // ==========================================================
    // DESELECTIONNER TOUTES LES TABLES
    // ==========================================================

    const deselectAll = () => {

        setSuccess("");

        setError("");

        setSelectedTables([]);

    };

    // ==========================================================
    // VERIFIER SI TOUT EST SELECTIONNE
    // ==========================================================

    const allSelected =
        tables.length > 0 &&
        selectedTables.length ===
            tables.length;

    // ==========================================================
    // SAUVEGARDER LES TABLES
    // ==========================================================

    const saveSelectedTables = async () => {

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
                "Veuillez sélectionner au moins une table."
            );

            return;

        }

        try {

            setSaving(true);

            setError("");

            setSuccess("");

            console.log(
                "TABLES SELECTIONNEES :",
                selectedTables
            );

            const response =
                await connectionsApi.saveTables(
                    connectionId,
                    selectedTables
                );

            console.log(
                "SAUVEGARDE TABLES :",
                response.data
            );

            /*
             * Sauvegarde également temporaire
             * côté frontend pour les pages qui
             * pourraient encore l'utiliser.
             */

            localStorage.setItem(
                `selected_tables_${connectionId}`,
                JSON.stringify(
                    selectedTables
                )
            );

            setSuccess(
                response.data?.message ||
                "Tables sélectionnées enregistrées avec succès."
            );

        } catch (err) {

            console.error(
                "Erreur sauvegarde tables :",
                err
            );

            setError(
                err.response?.data?.error ||
                err.response?.data?.message ||
                "Impossible d'enregistrer les tables sélectionnées."
            );

        } finally {

            setSaving(false);

        }

    };

    // ==========================================================
    // ANALYSE IA
    // ==========================================================

    const analyzeWithAI = async () => {

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
                "Veuillez sélectionner au moins une table."
            );

            return;

        }

        try {

            setSaving(true);

            setError("");

            setSuccess("");

            /*
             * On sauvegarde d'abord les tables
             * sélectionnées dans la BDD.
             */

            await connectionsApi.saveTables(
                connectionId,
                selectedTables
            );

            localStorage.setItem(
                `selected_tables_${connectionId}`,
                JSON.stringify(
                    selectedTables
                )
            );

            /*
             * Puis on lance l'analyse IA.
             */

            const response =
                await connectionsApi.analyze(
                    connectionId
                );

            console.log(
                "ANALYSE IA :",
                response.data
            );

            /*
             * Stockage temporaire du résultat
             * pour la page suivante.
             */

            localStorage.setItem(
                `ai_analysis_${connectionId}`,
                JSON.stringify(
                    response.data
                )
            );

            setSuccess(
                response.data?.message ||
                "Analyse IA terminée avec succès."
            );

            /*
             * Petit délai pour permettre à
             * l'utilisateur de voir le succès.
             */

            setTimeout(() => {

                navigate(
                    `/workspace/${projectId}`
                );

            }, 700);

        } catch (err) {

            console.error(
                "Erreur analyse IA :",
                err
            );

            setError(
                err.response?.data?.error ||
                err.response?.data?.message ||
                "Impossible de lancer l'analyse IA."
            );

        } finally {

            setSaving(false);

        }

    };

    // ==========================================================
    // RETOUR SCHEMA
    // ==========================================================

    const goBackToSchema = () => {

        navigate(
            `/workspace/${projectId}/schema/${connectionId}`
        );

    };

    // ==========================================================
    // RETOUR WORKSPACE
    // ==========================================================

    const goBackToWorkspace = () => {

        navigate(
            `/workspace/${projectId}`
        );

    };

    // ==========================================================
    // LOADING
    // ==========================================================

    if (loading) {

        return (

            <div className="page-container">

                <div className="card">

                    <div className="empty-state">

                        <div className="loading-spinner"></div>

                        <h2>
                            Chargement du schéma
                        </h2>

                        <p>
                            Récupération des tables
                            disponibles...
                        </p>

                    </div>

                </div>

            </div>

        );

    }

    // ==========================================================
    // ERROR
    // ==========================================================

    if (error && !schema) {

        return (

            <div className="page-container">

                <div className="card">

                    <h2>
                        Impossible de charger les tables
                    </h2>

                    <p className="status-error">
                        {error}
                    </p>

                    <div className="buttons-row">

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={
                                goBackToWorkspace
                            }
                        >
                            Retour au workspace
                        </button>

                        <button
                            type="button"
                            className="primary-btn"
                            onClick={loadSchema}
                        >
                            Réessayer
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

        <div className="page-container table-selection-page">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header">

                <div>

                    <div className="page-eyebrow">
                        ANALYSE DES DONNÉES
                    </div>

                    <h1>
                        Sélection des tables
                    </h1>

                    <p>
                        Choisissez les tables qui seront
                        utilisées pour l'analyse et la
                        génération des dashboards.
                    </p>

                </div>

                <div className="buttons-row">

                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={
                            goBackToSchema
                        }
                    >
                        Retour au schéma
                    </button>

                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={
                            goBackToWorkspace
                        }
                    >
                        Workspace
                    </button>

                </div>

            </div>


            {/* ==================================================
                MESSAGE ERREUR
            ================================================== */}

            {error && (

                <div className="status-message status-error">

                    {error}

                </div>

            )}


            {/* ==================================================
                MESSAGE SUCCES
            ================================================== */}

            {success && (

                <div className="status-message status-success">

                    {success}

                </div>

            )}


            {/* ==================================================
                CONTROLES
            ================================================== */}

            <div className="card">

                <div className="card-title">

                    <div>

                        <span className="card-kicker">
                            TABLES DISPONIBLES
                        </span>

                        <h2>
                            Choisissez vos sources
                        </h2>

                    </div>

                    <span className="count-badge">

                        {selectedTables.length}
                        {" / "}
                        {tables.length}

                    </span>

                </div>


                <div className="table-selection-toolbar">

                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={selectAll}
                        disabled={
                            tables.length === 0 ||
                            allSelected ||
                            saving
                        }
                    >
                        Tout sélectionner
                    </button>

                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={deselectAll}
                        disabled={
                            selectedTables.length === 0 ||
                            saving
                        }
                    >
                        Tout désélectionner
                    </button>

                </div>


                {/* ==================================================
                    AUCUNE TABLE
                ================================================== */}

                {tables.length === 0 ? (

                    <div className="empty-state">

                        <div className="empty-icon">
                            DB
                        </div>

                        <h3>
                            Aucune table disponible
                        </h3>

                        <p>
                            Le schéma ne contient aucune
                            table exploitable.
                        </p>

                    </div>

                ) : (

                    /* ==================================================
                       LISTE DES TABLES
                       ================================================== */

                    <div className="table-selection-list">

                        {tables.map(
                            (table, index) => {

                                const isSelected =
                                    selectedTables.includes(
                                        table.name
                                    );

                                return (

                                    <label
                                        key={`${table.name}-${index}`}
                                        className={
                                            isSelected
                                                ? "table-selection-item selected"
                                                : "table-selection-item"
                                        }
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
                                                saving
                                            }
                                        />


                                        <div className="table-selection-info">

                                            <div className="table-selection-name">

                                                <span className="table-icon">
                                                    ▣
                                                </span>

                                                <strong>
                                                    {table.name}
                                                </strong>

                                            </div>

                                            <span className="table-selection-columns">

                                                {table.columns.length}
                                                {" "}
                                                colonne
                                                {table.columns.length !== 1
                                                    ? "s"
                                                    : ""}

                                            </span>

                                        </div>


                                        <div className="table-selection-check">

                                            {isSelected
                                                ? "✓"
                                                : ""}

                                        </div>

                                    </label>

                                );

                            }
                        )}

                    </div>

                )}

            </div>


            {/* ==================================================
                RESUME
            ================================================== */}

            {tables.length > 0 && (

                <div className="card">

                    <div className="card-title">

                        <h2>
                            Résumé de la sélection
                        </h2>

                    </div>

                    <div className="selection-summary">

                        <div className="summary-item">

                            <span>
                                Tables disponibles
                            </span>

                            <strong>
                                {tables.length}
                            </strong>

                        </div>


                        <div className="summary-item">

                            <span>
                                Tables sélectionnées
                            </span>

                            <strong>
                                {selectedTables.length}
                            </strong>

                        </div>


                        <div className="summary-item">

                            <span>
                                Colonnes sélectionnées
                            </span>

                            <strong>

                                {tables
                                    .filter(
                                        (table) =>
                                            selectedTables.includes(
                                                table.name
                                            )
                                    )
                                    .reduce(
                                        (
                                            total,
                                            table
                                        ) =>
                                            total +
                                            table.columns.length,
                                        0
                                    )}

                            </strong>

                        </div>

                    </div>

                </div>

            )}


            {/* ==================================================
                ACTIONS FINALES
            ================================================== */}

            <div className="card table-selection-actions">

                <div>

                    <h2>
                        Prêt pour l'analyse ?
                    </h2>

                    <p>
                        Enregistrez votre sélection puis
                        lancez l'analyse IA du schéma.
                    </p>

                </div>


                <div className="buttons-row">

                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={
                            saveSelectedTables
                        }
                        disabled={
                            saving ||
                            selectedTables.length === 0
                        }
                    >

                        {saving
                            ? "Enregistrement..."
                            : "Enregistrer la sélection"
                        }

                    </button>


                    <button
                        type="button"
                        className="primary-btn"
                        onClick={
                            analyzeWithAI
                        }
                        disabled={
                            saving ||
                            selectedTables.length === 0
                        }
                    >

                        {saving
                            ? "Analyse..."
                            : "Analyser avec l'IA"
                        }

                    </button>

                </div>

            </div>

        </div>

    );

};

export default TableSelectionPage;