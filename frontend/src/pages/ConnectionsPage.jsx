// src/pages/ConnectionsPage.jsx

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const ConnectionsPage = () => {
    const navigate = useNavigate();
    const { projectId } = useParams();

    // ==========================================================
    // ETATS
    // ==========================================================

    const [connections, setConnections] = useState([]);

    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [deleting, setDeleting] = useState(null);

    const [selectedConnection, setSelectedConnection] = useState(null);

    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState("");

    const [newConnection, setNewConnection] = useState({
        nom: "",
        engine_type: "sqlite",
        host: "",
        port: "",
        database_name: "",
        username: "",
        password: "",
    });

    const [sqliteFile, setSqliteFile] = useState(null);

    // ==========================================================
    // URL API
    // ==========================================================

    const API_URL = projectId
        ? `/api/connections/project/${projectId}`
        : null;

    // ==========================================================
    // TOKEN
    // ==========================================================

    const getToken = () => {
        return localStorage.getItem("token");
    };

    // ==========================================================
    // MESSAGE
    // ==========================================================

    const showMessage = (text, type = "error") => {
        setMessage(text);
        setMessageType(type);
    };

    // ==========================================================
    // CHARGER LES CONNEXIONS
    // ==========================================================

    const loadConnections = async () => {
        if (!projectId) {
            showMessage(
                "Aucun projet sélectionné.",
                "error"
            );

            setLoading(false);
            return;
        }

        try {
            setLoading(true);

            const token = getToken();

            if (!token) {
                showMessage(
                    "Utilisateur non connecté.",
                    "error"
                );

                return;
            }

            const response = await fetch(API_URL, {
                method: "GET",

                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            const contentType =
                response.headers.get("content-type") || "";

            let data;

            if (contentType.includes("application/json")) {
                data = await response.json();
            } else {
                const text = await response.text();

                console.error(
                    "Réponse non JSON :",
                    text
                );

                throw new Error(
                    `Réponse serveur non JSON (${response.status})`
                );
            }

            console.log(
                "LIST CONNECTIONS:",
                data
            );

            if (!response.ok) {
                showMessage(
                    data.error ||
                    data.message ||
                    "Impossible de charger les connexions.",
                    "error"
                );

                return;
            }

            const list = Array.isArray(data)
                ? data
                : data.connections || [];

            setConnections(list);

            // Désélectionner si la connexion n'existe plus
            if (
                selectedConnection &&
                !list.some(
                    (connection) =>
                        String(connection.id) ===
                        String(selectedConnection.id)
                )
            ) {
                setSelectedConnection(null);
            }

        } catch (error) {
            console.error(
                "Erreur chargement connexions:",
                error
            );

            showMessage(
                error.message ||
                "Impossible de contacter le serveur.",
                "error"
            );

        } finally {
            setLoading(false);
        }
    };

    // ==========================================================
    // INITIALISATION
    // ==========================================================

    useEffect(() => {
        loadConnections();
    }, [projectId]);

    // ==========================================================
    // CHANGEMENT FORMULAIRE
    // ==========================================================

    const handleChange = (event) => {
        const {
            name,
            value,
        } = event.target;

        setNewConnection((previous) => ({
            ...previous,
            [name]: value,
        }));

        setMessage("");
        setMessageType("");
    };

    // ==========================================================
    // CHANGEMENT TYPE BDD
    // ==========================================================

    const handleEngineChange = (event) => {
        const engineType = event.target.value;

        setNewConnection((previous) => ({
            ...previous,
            engine_type: engineType,
        }));

        setSqliteFile(null);

        setMessage("");
        setMessageType("");
    };

    // ==========================================================
    // FICHIER SQLITE
    // ==========================================================

    const handleSqliteFileChange = (event) => {
        const file = event.target.files?.[0] || null;

        setSqliteFile(file);

        setMessage("");
        setMessageType("");
    };

    // ==========================================================
    // VALIDATION
    // ==========================================================

    const validateForm = () => {
        const nom = newConnection.nom.trim();

        if (!nom) {
            return "Le nom de la connexion est obligatoire.";
        }

        if (!newConnection.engine_type) {
            return "Le type de base de données est obligatoire.";
        }

        // ------------------------------------------------------
        // SQLITE
        // ------------------------------------------------------

        if (
            newConnection.engine_type === "sqlite"
        ) {
            if (!sqliteFile) {
                return "Veuillez sélectionner un fichier SQLite.";
            }

            const filename =
                sqliteFile.name.toLowerCase();

            const validExtension =
                filename.endsWith(".db") ||
                filename.endsWith(".sqlite") ||
                filename.endsWith(".sqlite3");

            if (!validExtension) {
                return (
                    "Fichier SQLite invalide. " +
                    "Utilisez .db, .sqlite ou .sqlite3."
                );
            }

            return null;
        }

        // ------------------------------------------------------
        // BASE SERVEUR
        // ------------------------------------------------------

        const requiredFields = [
            ["host", "Le serveur est obligatoire."],
            ["port", "Le port est obligatoire."],
            [
                "database_name",
                "Le nom de la base est obligatoire.",
            ],
            [
                "username",
                "Le nom d'utilisateur est obligatoire.",
            ],
            [
                "password",
                "Le mot de passe est obligatoire.",
            ],
        ];

        for (const [
            field,
            errorMessage,
        ] of requiredFields) {
            if (
                !String(
                    newConnection[field] || ""
                ).trim()
            ) {
                return errorMessage;
            }
        }

        if (
            !Number.isInteger(
                Number(newConnection.port)
            )
        ) {
            return "Le port doit être un nombre.";
        }

        return null;
    };

    // ==========================================================
    // CREER UNE CONNEXION
    // ==========================================================

    const createConnection = async () => {
        if (!projectId) {
            showMessage(
                "Projet invalide.",
                "error"
            );

            return;
        }

        const validationError =
            validateForm();

        if (validationError) {
            showMessage(
                validationError,
                "error"
            );

            return;
        }

        try {
            setCreating(true);

            setMessage("");
            setMessageType("");

            const token = getToken();

            if (!token) {
                showMessage(
                    "Vous devez être connecté.",
                    "error"
                );

                return;
            }

            let response;

            // ==================================================
            // SQLITE
            // ==================================================

            if (
                newConnection.engine_type ===
                "sqlite"
            ) {
                const formData = new FormData();

                formData.append(
                    "nom",
                    newConnection.nom.trim()
                );

                formData.append(
                    "engine_type",
                    "sqlite"
                );

                formData.append(
                    "file",
                    sqliteFile
                );

                response = await fetch(
                    API_URL,
                    {
                        method: "POST",

                        headers: {
                            Authorization:
                                `Bearer ${token}`,
                        },

                        body: formData,
                    }
                );
            }

            // ==================================================
            // MYSQL / POSTGRESQL / SQL SERVER
            // ==================================================

            else {
                const payload = {
                    nom:
                        newConnection.nom.trim(),

                    engine_type:
                        newConnection.engine_type,

                    host:
                        newConnection.host.trim(),

                    port:
                        Number(newConnection.port),

                    database_name:
                        newConnection.database_name.trim(),

                    username:
                        newConnection.username.trim(),

                    password:
                        newConnection.password,
                };

                response = await fetch(
                    API_URL,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            Authorization:
                                `Bearer ${token}`,
                        },

                        body:
                            JSON.stringify(
                                payload
                            ),
                    }
                );
            }

            // ==================================================
            // REPONSE
            // ==================================================

            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";

            let data;

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

                console.error(
                    "Réponse création non JSON:",
                    text
                );

                throw new Error(
                    `Réponse serveur non JSON (${response.status})`
                );
            }

            console.log(
                "CREATE CONNECTION RESPONSE:",
                data
            );

            if (!response.ok) {
                showMessage(
                    data.error ||
                    data.message ||
                    "Erreur lors de la création de la connexion.",
                    "error"
                );

                return;
            }

            // ==================================================
            // RESET FORMULAIRE
            // ==================================================

            setNewConnection({
                nom: "",
                engine_type: "sqlite",
                host: "",
                port: "",
                database_name: "",
                username: "",
                password: "",
            });

            setSqliteFile(null);

            // Réinitialiser input fichier
            const fileInput =
                document.getElementById(
                    "sqlite-file"
                );

            if (fileInput) {
                fileInput.value = "";
            }

            showMessage(
                "Connexion créée avec succès.",
                "success"
            );

            // ==================================================
            // RECHARGER
            // ==================================================

            await loadConnections();

        } catch (error) {
            console.error(
                "Erreur création connexion:",
                error
            );

            showMessage(
                error.message ||
                "Impossible de contacter le serveur.",
                "error"
            );

        } finally {
            setCreating(false);
        }
    };

    // ==========================================================
    // SELECTIONNER
    // ==========================================================

    const selectConnection = (connection) => {
        setSelectedConnection(connection);

        showMessage(
            `Connexion "${connection.nom || connection.name || "Connexion"}" sélectionnée.`,
            "success"
        );
    };

    // ==========================================================
    // SUPPRIMER
    // ==========================================================

    const deleteConnection = async (connection) => {
        if (!connection?.id) {
            return;
        }

        const connectionName =
            connection.nom ||
            connection.name ||
            "cette connexion";

        const confirmed =
            window.confirm(
                `Voulez-vous vraiment supprimer "${connectionName}" ?\n\nCette action est définitive.`
            );

        if (!confirmed) {
            return;
        }

        try {
            setDeleting(connection.id);

            setMessage("");
            setMessageType("");

            const token = getToken();

            if (!token) {
                showMessage(
                    "Vous devez être connecté.",
                    "error"
                );

                return;
            }

            const response = await fetch(
                `/api/connections/${connection.id}`,
                {
                    method: "DELETE",

                    headers: {
                        Authorization:
                            `Bearer ${token}`,
                    },
                }
            );

            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";

            let data = {};

            if (
                contentType.includes(
                    "application/json"
                )
            ) {
                data =
                    await response.json();
            }

            console.log(
                "DELETE CONNECTION RESPONSE:",
                data
            );

            if (!response.ok) {
                showMessage(
                    data.error ||
                    data.message ||
                    "Impossible de supprimer la connexion.",
                    "error"
                );

                return;
            }

            // Si c'était la connexion sélectionnée
            if (
                selectedConnection &&
                String(
                    selectedConnection.id
                ) ===
                    String(connection.id)
            ) {
                setSelectedConnection(null);
            }

            // Retirer immédiatement de l'interface
            setConnections(
                (previous) =>
                    previous.filter(
                        (item) =>
                            String(item.id) !==
                            String(connection.id)
                    )
            );

            showMessage(
                "Connexion supprimée définitivement.",
                "success"
            );

            // Vérification avec le backend
            await loadConnections();

        } catch (error) {
            console.error(
                "Erreur suppression connexion:",
                error
            );

            showMessage(
                error.message ||
                "Impossible de supprimer la connexion.",
                "error"
            );

        } finally {
            setDeleting(null);
        }
    };

    // ==========================================================
    // RETOUR WORKSPACE
    // ==========================================================

    const openWorkspace = () => {
        if (!projectId) {
            return;
        }

        navigate(
            `/workspace/${projectId}`
        );
    };

    // ==========================================================
    // OUVRIR SCHEMA
    // ==========================================================

    const openSchema = (connectionId) => {
        if (!projectId || !connectionId) {
            return;
        }

        navigate(
            `/workspace/${projectId}/schema/${connectionId}`
        );
    };

    // ==========================================================
    // CREER DASHBOARD
    // ==========================================================

    const configureDashboard = () => {
        if (!selectedConnection?.id) {
            showMessage(
                "Veuillez sélectionner une connexion.",
                "error"
            );

            return;
        }

        navigate(
            `/workspace/${projectId}/schema/${selectedConnection.id}?dashboard=true`
        );
    };

    // ==========================================================
    // NOM MOTEUR
    // ==========================================================

    const getEngineLabel = (engine) => {
        const labels = {
            sqlite: "SQLite",
            mysql: "MySQL",
            postgresql: "PostgreSQL",
            mssql: "SQL Server",
        };

        return (
            labels[
                String(engine || "").toLowerCase()
            ] ||
            engine ||
            "Base de données"
        );
    };

    // ==========================================================
    // RENDER
    // ==========================================================

    return (
        <div className="page-container connections-page">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header connections-header">

                <div>

                    <div className="page-eyebrow">
                        PROJET
                    </div>

                    <h1>
                        Connexions BDD
                    </h1>

                    <p>
                        Gérez les sources de données
                        associées à ce projet.
                    </p>

                </div>

                <button
                    type="button"
                    className="secondary-btn"
                    onClick={openWorkspace}
                >
                    Retour au workspace
                </button>

            </div>


            {/* ==================================================
                CONNEXION SELECTIONNEE
            ================================================== */}

            {selectedConnection && (

                <div className="card selected-connection-card">

                    <div>

                        <span className="card-kicker">
                            CONNEXION SÉLECTIONNÉE
                        </span>

                        <h2>
                            {selectedConnection.nom ||
                                selectedConnection.name ||
                                "Connexion"}
                        </h2>

                        <p>
                            {getEngineLabel(
                                selectedConnection.engine_type ||
                                selectedConnection.engine
                            )}
                        </p>

                    </div>

                    <div className="selected-connection-actions">

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={() =>
                                openSchema(
                                    selectedConnection.id
                                )
                            }
                        >
                            Explorer les tables
                        </button>

                        <button
                            type="button"
                            className="primary-btn"
                            onClick={
                                configureDashboard
                            }
                        >
                            Créer le dashboard
                        </button>

                    </div>

                </div>
            )}


            {/* ==================================================
                CONTENU
            ================================================== */}

            <div className="connections-layout">


                {/* ==================================================
                    CREATION
                ================================================== */}

                <div className="card connection-create-card">

                    <div className="card-title">

                        <div>

                            <span className="card-kicker">
                                SOURCE DE DONNÉES
                            </span>

                            <h2>
                                Nouvelle connexion
                            </h2>

                        </div>

                        <span className="card-icon">
                            +
                        </span>

                    </div>


                    {/* ==================================================
                        NOM
                    ================================================== */}

                    <div className="form-group">

                        <label htmlFor="connection-name">
                            Nom de la connexion
                        </label>

                        <input
                            id="connection-name"
                            name="nom"
                            type="text"
                            placeholder="Ex : Base commerciale"
                            value={
                                newConnection.nom
                            }
                            onChange={
                                handleChange
                            }
                            disabled={
                                creating
                            }
                        />

                    </div>


                    {/* ==================================================
                        TYPE BDD
                    ================================================== */}

                    <div className="form-group">

                        <label htmlFor="engine-type">
                            Type de base de données
                        </label>

                        <select
                            id="engine-type"
                            name="engine_type"
                            value={
                                newConnection.engine_type
                            }
                            onChange={
                                handleEngineChange
                            }
                            disabled={
                                creating
                            }
                        >

                            <option value="sqlite">
                                SQLite
                            </option>

                            <option value="mysql">
                                MySQL
                            </option>

                            <option value="postgresql">
                                PostgreSQL
                            </option>

                            <option value="mssql">
                                SQL Server
                            </option>

                        </select>

                    </div>


                    {/* ==================================================
                        SQLITE
                    ================================================== */}

                    {newConnection.engine_type ===
                        "sqlite" && (

                        <div className="form-group">

                            <label htmlFor="sqlite-file">
                                Fichier SQLite
                            </label>

                            <input
                                id="sqlite-file"
                                type="file"
                                accept=".db,.sqlite,.sqlite3"
                                onChange={
                                    handleSqliteFileChange
                                }
                                disabled={
                                    creating
                                }
                            />

                            {sqliteFile && (

                                <small>
                                    Fichier sélectionné :
                                    {" "}
                                    {sqliteFile.name}
                                </small>

                            )}

                        </div>

                    )}


                    {/* ==================================================
                        BASE SERVEUR
                    ================================================== */}

                    {newConnection.engine_type !==
                        "sqlite" && (

                        <>

                            <div className="form-group">

                                <label htmlFor="connection-host">
                                    Serveur
                                </label>

                                <input
                                    id="connection-host"
                                    name="host"
                                    type="text"
                                    placeholder="Ex : localhost"
                                    value={
                                        newConnection.host
                                    }
                                    onChange={
                                        handleChange
                                    }
                                    disabled={
                                        creating
                                    }
                                />

                            </div>


                            <div className="form-group">

                                <label htmlFor="connection-port">
                                    Port
                                </label>

                                <input
                                    id="connection-port"
                                    name="port"
                                    type="number"
                                    placeholder={
                                        newConnection.engine_type ===
                                        "mysql"
                                            ? "3306"
                                            : newConnection.engine_type ===
                                              "postgresql"
                                                ? "5432"
                                                : "1433"
                                    }
                                    value={
                                        newConnection.port
                                    }
                                    onChange={
                                        handleChange
                                    }
                                    disabled={
                                        creating
                                    }
                                />

                            </div>


                            <div className="form-group">

                                <label htmlFor="database-name">
                                    Nom de la base
                                </label>

                                <input
                                    id="database-name"
                                    name="database_name"
                                    type="text"
                                    placeholder="Nom de la base"
                                    value={
                                        newConnection.database_name
                                    }
                                    onChange={
                                        handleChange
                                    }
                                    disabled={
                                        creating
                                    }
                                />

                            </div>


                            <div className="form-group">

                                <label htmlFor="database-username">
                                    Utilisateur
                                </label>

                                <input
                                    id="database-username"
                                    name="username"
                                    type="text"
                                    placeholder="Utilisateur"
                                    value={
                                        newConnection.username
                                    }
                                    onChange={
                                        handleChange
                                    }
                                    disabled={
                                        creating
                                    }
                                />

                            </div>


                            <div className="form-group">

                                <label htmlFor="database-password">
                                    Mot de passe
                                </label>

                                <input
                                    id="database-password"
                                    name="password"
                                    type="password"
                                    placeholder="Mot de passe"
                                    value={
                                        newConnection.password
                                    }
                                    onChange={
                                        handleChange
                                    }
                                    disabled={
                                        creating
                                    }
                                />

                            </div>

                        </>

                    )}


                    {/* ==================================================
                        CREER
                    ================================================== */}

                    <button
                        type="button"
                        className="primary-btn"
                        onClick={
                            createConnection
                        }
                        disabled={
                            creating
                        }
                    >
                        {creating
                            ? "Création..."
                            : "Ajouter la connexion"}
                    </button>


                    {/* ==================================================
                        MESSAGE
                    ================================================== */}

                    {message && (

                        <div
                            className={`status-message ${
                                messageType ===
                                "success"
                                    ? "success"
                                    : "error"
                            }`}
                        >
                            {message}
                        </div>

                    )}

                </div>


                {/* ==================================================
                    LISTE
                ================================================== */}

                <div className="card connection-list-card">

                    <div className="card-title">

                        <div>

                            <span className="card-kicker">
                                SOURCES CONNECTÉES
                            </span>

                            <h2>
                                Vos connexions
                            </h2>

                        </div>

                        <span className="count-badge">
                            {connections.length}
                        </span>

                    </div>


                    {/* ==================================================
                        LOADING
                    ================================================== */}

                    {loading ? (

                        <div className="empty-state">

                            <div className="loading-spinner"></div>

                            <p>
                                Chargement des connexions...
                            </p>

                        </div>

                    ) : connections.length === 0 ? (

                        <div className="empty-state">

                            <div className="empty-icon">
                                DB
                            </div>

                            <h3>
                                Aucune connexion
                            </h3>

                            <p>
                                Ajoutez une source de données
                                pour commencer votre analyse.
                            </p>

                        </div>

                    ) : (

                        <div className="connections-list">

                            {connections.map(
                                (connection) => {

                                    const isSelected =
                                        selectedConnection &&
                                        String(
                                            selectedConnection.id
                                        ) ===
                                            String(
                                                connection.id
                                            );

                                    const isDeleting =
                                        deleting ===
                                        connection.id;

                                    return (

                                        <div
                                            className={`connection-item ${
                                                isSelected
                                                    ? "selected"
                                                    : ""
                                            }`}
                                            key={
                                                connection.id
                                            }
                                        >

                                            {/* ICON */}

                                            <div className="connection-icon">
                                                DB
                                            </div>


                                            {/* INFOS */}

                                            <div className="connection-info">

                                                <h3>
                                                    {connection.nom ||
                                                        connection.name ||
                                                        "Connexion"}
                                                </h3>

                                                <p>
                                                    {getEngineLabel(
                                                        connection.engine_type ||
                                                        connection.engine
                                                    )}
                                                </p>

                                                <small>
                                                    {connection.created_at
                                                        ? new Date(
                                                            connection.created_at
                                                        ).toLocaleDateString(
                                                            "fr-FR"
                                                        )
                                                        : "Connexion active"}
                                                </small>

                                            </div>


                                            {/* ACTIONS */}

                                            <div className="connection-actions">

                                                <button
                                                    type="button"
                                                    className={
                                                        isSelected
                                                            ? "primary-btn"
                                                            : "secondary-btn"
                                                    }
                                                    onClick={() =>
                                                        selectConnection(
                                                            connection
                                                        )
                                                    }
                                                    disabled={
                                                        isDeleting
                                                    }
                                                >
                                                    {isSelected
                                                        ? "Sélectionnée"
                                                        : "Sélectionner"}
                                                </button>


                                                <button
                                                    type="button"
                                                    className="secondary-btn"
                                                    onClick={() =>
                                                        openSchema(
                                                            connection.id
                                                        )
                                                    }
                                                    disabled={
                                                        isDeleting
                                                    }
                                                >
                                                    Explorer
                                                </button>


                                                <button
                                                    type="button"
                                                    className="danger-btn"
                                                    onClick={() =>
                                                        deleteConnection(
                                                            connection
                                                        )
                                                    }
                                                    disabled={
                                                        isDeleting
                                                    }
                                                >
                                                    {isDeleting
                                                        ? "Suppression..."
                                                        : "Supprimer"}
                                                </button>

                                            </div>

                                        </div>

                                    );
                                }
                            )}

                        </div>

                    )}

                </div>

            </div>

        </div>
    );
};

export default ConnectionsPage;