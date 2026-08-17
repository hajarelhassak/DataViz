// src/pages/ConnectionPage.jsx

import React, { useState } from "react";
import {
    useNavigate,
    useParams,
} from "react-router-dom";


// ==========================================================
// COMPOSANT
// ==========================================================

const ConnectionPage = () => {

    const navigate = useNavigate();

    const { projectId } = useParams();


    // ==========================================================
    // ETATS
    // ==========================================================

    const [form, setForm] = useState({

        nom: "",

        engine_type: "postgresql",

        host: "localhost",

        port: "5432",

        username: "",

        password: "",

        database: "",

    });


    const [sqliteFile, setSqliteFile] =
        useState(null);


    const [testing, setTesting] =
        useState(false);


    const [saving, setSaving] =
        useState(false);


    const [message, setMessage] =
        useState("");


    const [error, setError] =
        useState("");


    // ==========================================================
    // OPTIONS BDD
    // ==========================================================

    const ENGINE_OPTIONS = [

        {
            value: "postgresql",
            label: "PostgreSQL",
        },

        {
            value: "mysql",
            label: "MySQL",
        },

        {
            value: "mssql",
            label: "SQL Server",
        },

        {
            value: "sqlite",
            label: "SQLite",
        },

    ];


    // ==========================================================
    // CHANGEMENT FORMULAIRE
    // ==========================================================

    const handleChange = (event) => {

        const {
            name,
            value,
        } = event.target;


        setForm((previous) => ({

            ...previous,

            [name]: value,

        }));


        setMessage("");

        setError("");

    };


    // ==========================================================
    // CHANGEMENT FICHIER SQLITE
    // ==========================================================

    const handleFileChange = (event) => {

        const file =
            event.target.files?.[0] || null;


        setSqliteFile(file);

        setMessage("");

        setError("");

    };


    // ==========================================================
    // CHANGEMENT TYPE BDD
    // ==========================================================

    const handleEngineChange = (event) => {

        const engine =
            event.target.value;


        let defaultPort = "5432";


        if (engine === "mysql") {

            defaultPort = "3306";

        }


        if (engine === "mssql") {

            defaultPort = "1433";

        }


        setForm((previous) => ({

            ...previous,

            engine_type: engine,

            port:
                engine === "sqlite"
                    ? ""
                    : defaultPort,

        }));


        setMessage("");

        setError("");

    };


    // ==========================================================
    // VALIDATION
    // ==========================================================

    const validateForm = () => {

        if (!projectId) {

            setError(
                "Projet invalide."
            );

            return false;

        }


        if (!form.nom.trim()) {

            setError(
                "Le nom de la connexion est obligatoire."
            );

            return false;

        }


        if (form.engine_type === "sqlite") {

            if (!sqliteFile) {

                setError(
                    "Veuillez sélectionner un fichier SQLite."
                );

                return false;

            }

            return true;

        }


        if (!form.host.trim()) {

            setError(
                "Le serveur est obligatoire."
            );

            return false;

        }


        if (!form.database.trim()) {

            setError(
                "Le nom de la base de données est obligatoire."
            );

            return false;

        }


        return true;

    };


    // ==========================================================
    // LECTURE REPONSE
    // ==========================================================

    const parseResponse = async (response) => {

        const contentType =
            response.headers.get(
                "content-type"
            ) || "";


        if (
            contentType.includes(
                "application/json"
            )
        ) {

            return await response.json();

        }


        const text =
            await response.text();


        throw new Error(
            text ||
            `Réponse serveur non JSON (${response.status}).`
        );

    };


    // ==========================================================
    // TESTER LA CONNEXION
    // ==========================================================

    const testConnection = async () => {

        if (!validateForm()) {

            return;

        }


        const token =
            localStorage.getItem("token");


        if (!token) {

            setError(
                "Vous devez être connecté."
            );

            return;

        }


        try {

            setTesting(true);

            setMessage("");

            setError("");


            let response;


            // ==================================================
            // SQLITE
            // ==================================================

            if (
                form.engine_type === "sqlite"
            ) {

                const formData =
                    new FormData();


                formData.append(
                    "nom",
                    form.nom.trim()
                );


                formData.append(
                    "engine_type",
                    "sqlite"
                );


                formData.append(
                    "file",
                    sqliteFile
                );


                response =
                    await fetch(
                        "/api/connections/test",
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
            // AUTRES BDD
            // ==================================================

            else {

                response =
                    await fetch(
                        "/api/connections/test",
                        {
                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json",

                                Authorization:
                                    `Bearer ${token}`,

                            },

                            body: JSON.stringify({

                                nom:
                                    form.nom.trim(),

                                engine_type:
                                    form.engine_type,

                                host:
                                    form.host.trim(),

                                port:
                                    form.port,

                                username:
                                    form.username,

                                password:
                                    form.password,

                                database:
                                    form.database.trim(),

                            }),

                        }
                    );

            }


            const data =
                await parseResponse(
                    response
                );


            if (!response.ok) {

                throw new Error(

                    data?.error ||

                    data?.message ||

                    "Échec du test de connexion."

                );

            }


            setMessage(

                data?.message ||

                "Connexion réussie."

            );


        } catch (err) {

            console.error(
                "Erreur test connexion :",
                err
            );


            setError(

                err.message ||

                "Impossible de tester la connexion."

            );

        } finally {

            setTesting(false);

        }

    };


    // ==========================================================
    // SAUVEGARDER LA CONNEXION
    // ==========================================================

    const saveConnection = async () => {

        if (!validateForm()) {

            return;

        }


        const token =
            localStorage.getItem("token");


        if (!token) {

            setError(
                "Vous devez être connecté."
            );

            return;

        }


        try {

            setSaving(true);

            setMessage("");

            setError("");


            let response;


            // ==================================================
            // SQLITE
            // ==================================================

            if (
                form.engine_type === "sqlite"
            ) {

                const formData =
                    new FormData();


                formData.append(
                    "project_id",
                    projectId
                );


                formData.append(
                    "nom",
                    form.nom.trim()
                );


                formData.append(
                    "engine_type",
                    "sqlite"
                );


                formData.append(
                    "file",
                    sqliteFile
                );


                response =
                    await fetch(
                        "/api/connections",
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

                response =
                    await fetch(
                        "/api/connections",
                        {
                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json",

                                Authorization:
                                    `Bearer ${token}`,

                            },

                            body: JSON.stringify({

                                project_id:
                                    projectId,

                                nom:
                                    form.nom.trim(),

                                engine_type:
                                    form.engine_type,

                                host:
                                    form.host.trim(),

                                port:
                                    form.port,

                                username:
                                    form.username,

                                password:
                                    form.password,

                                database:
                                    form.database.trim(),

                            }),

                        }
                    );

            }


            const data =
                await parseResponse(
                    response
                );


            if (!response.ok) {

                throw new Error(

                    data?.error ||

                    data?.message ||

                    "Erreur lors de la sauvegarde."

                );

            }


            // ==================================================
            // RECUPERATION CONNEXION
            // ==================================================

            const connection =
                data?.connection ||
                data?.data ||
                data;


            const connectionId =
                connection?.id ||
                connection?.connection_id;


            console.log(
                "CONNEXION CREEE :",
                connection
            );


            console.log(
                "CONNECTION ID :",
                connectionId
            );


            if (!connectionId) {

                throw new Error(
                    "La connexion a été créée mais le serveur n'a pas retourné son identifiant."
                );

            }


            // ==================================================
            // SAUVEGARDE LOCALE
            // ==================================================

            sessionStorage.setItem(

                `dataviz_selected_connection_${projectId}`,

                String(connectionId)

            );


            sessionStorage.setItem(

                `dataviz_selected_tables_${projectId}`,

                JSON.stringify([])

            );


            // ==================================================
            // MESSAGE
            // ==================================================

            setMessage(
                "Connexion enregistrée avec succès."
            );


            // ==================================================
            // ALLER VERS LE SCHEMA
            // ==================================================

            navigate(

                `/workspace/${projectId}/schema/${connectionId}`,

                {

                    state: {

                        connectionId:
                            connectionId,

                        selectedTables: [],

                        projectId:
                            projectId,

                    },

                }

            );


        } catch (err) {

            console.error(
                "Erreur sauvegarde connexion :",
                err
            );


            setError(

                err.message ||

                "Impossible de sauvegarder la connexion."

            );

        } finally {

            setSaving(false);

        }

    };


    // ==========================================================
    // RETOUR
    // ==========================================================

    const goBack = () => {

        navigate(
            `/connections/${projectId}`
        );

    };


    // ==========================================================
    // RENDER
    // ==========================================================

    return (

        <div className="page-container connection-page">


            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header">

                <div>

                    <div className="page-eyebrow">
                        SOURCE DE DONNÉES
                    </div>

                    <h1>
                        Nouvelle connexion
                    </h1>

                    <p>
                        Configurez la connexion à votre
                        source de données.
                    </p>

                </div>


                <button
                    type="button"
                    className="secondary-btn"
                    onClick={goBack}
                >
                    Retour aux connexions
                </button>

            </div>


            {/* ==================================================
                FORMULAIRE
            ================================================== */}

            <div className="card">


                {/* NOM */}

                <div className="form-group">

                    <label htmlFor="connection-name">

                        Nom de la connexion

                    </label>


                    <input
                        id="connection-name"
                        name="nom"
                        type="text"
                        value={form.nom}
                        onChange={handleChange}
                        placeholder="Ex : Base commerciale"
                        disabled={
                            testing ||
                            saving
                        }
                    />

                </div>


                {/* TYPE BDD */}

                <div className="form-group">

                    <label htmlFor="engine_type">

                        Type de base de données

                    </label>


                    <select
                        id="engine_type"
                        name="engine_type"
                        value={form.engine_type}
                        onChange={
                            handleEngineChange
                        }
                        disabled={
                            testing ||
                            saving
                        }
                    >

                        {ENGINE_OPTIONS.map(
                            (option) => (

                                <option
                                    key={
                                        option.value
                                    }
                                    value={
                                        option.value
                                    }
                                >
                                    {option.label}
                                </option>

                            )
                        )}

                    </select>

                </div>


                {/* ==================================================
                    SQLITE
                ================================================== */}

                {form.engine_type === "sqlite" ? (

                    <div className="form-group">

                        <label htmlFor="sqlite-file">

                            Fichier SQLite

                        </label>


                        <input
                            id="sqlite-file"
                            type="file"
                            accept=".db,.sqlite,.sqlite3"
                            onChange={
                                handleFileChange
                            }
                            disabled={
                                testing ||
                                saving
                            }
                        />


                        {sqliteFile && (

                            <small>

                                Fichier :
                                {" "}
                                {sqliteFile.name}

                            </small>

                        )}

                    </div>

                ) : (

                    <>

                        {/* SERVEUR */}

                        <div className="form-group">

                            <label htmlFor="host">
                                Serveur
                            </label>


                            <input
                                id="host"
                                name="host"
                                type="text"
                                value={form.host}
                                onChange={
                                    handleChange
                                }
                                placeholder="localhost"
                                disabled={
                                    testing ||
                                    saving
                                }
                            />

                        </div>


                        {/* PORT */}

                        <div className="form-group">

                            <label htmlFor="port">
                                Port
                            </label>


                            <input
                                id="port"
                                name="port"
                                type="text"
                                value={form.port}
                                onChange={
                                    handleChange
                                }
                                disabled={
                                    testing ||
                                    saving
                                }
                            />

                        </div>


                        {/* USERNAME */}

                        <div className="form-group">

                            <label htmlFor="username">
                                Utilisateur
                            </label>


                            <input
                                id="username"
                                name="username"
                                type="text"
                                value={
                                    form.username
                                }
                                onChange={
                                    handleChange
                                }
                                disabled={
                                    testing ||
                                    saving
                                }
                            />

                        </div>


                        {/* PASSWORD */}

                        <div className="form-group">

                            <label htmlFor="password">
                                Mot de passe
                            </label>


                            <input
                                id="password"
                                name="password"
                                type="password"
                                value={
                                    form.password
                                }
                                onChange={
                                    handleChange
                                }
                                disabled={
                                    testing ||
                                    saving
                                }
                            />

                        </div>


                        {/* DATABASE */}

                        <div className="form-group">

                            <label htmlFor="database">
                                Base de données
                            </label>


                            <input
                                id="database"
                                name="database"
                                type="text"
                                value={
                                    form.database
                                }
                                onChange={
                                    handleChange
                                }
                                placeholder="Nom de la base"
                                disabled={
                                    testing ||
                                    saving
                                }
                            />

                        </div>

                    </>

                )}


                {/* ==================================================
                    MESSAGES
                ================================================== */}

                {message && (

                    <div className="status-message">
                        {message}
                    </div>

                )}


                {error && (

                    <div className="status-error">
                        {error}
                    </div>

                )}


                {/* ==================================================
                    ACTIONS
                ================================================== */}

                <div className="buttons-row">


                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={
                            testConnection
                        }
                        disabled={
                            testing ||
                            saving
                        }
                    >

                        {testing

                            ? "Test en cours..."

                            : "Tester la connexion"

                        }

                    </button>


                    <button
                        type="button"
                        className="primary-btn"
                        onClick={
                            saveConnection
                        }
                        disabled={
                            testing ||
                            saving
                        }
                    >

                        {saving

                            ? "Enregistrement..."

                            : "Enregistrer"

                        }

                    </button>

                </div>

            </div>

        </div>

    );

};


export default ConnectionPage;