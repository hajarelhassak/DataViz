import { useState } from "react";
import { useAuth } from "../context/AuthContext";

const SettingsPage = () => {
    const { user, logout } = useAuth();

    const [name, setName] = useState(
        user?.name || ""
    );

    const [email, setEmail] = useState(
        user?.email || ""
    );

    const [language, setLanguage] = useState("fr");

    const [notifications, setNotifications] = useState(true);

    const [message, setMessage] = useState("");

    // ==========================================================
    // SAUVEGARDER
    // ==========================================================

    const handleSave = (event) => {
        event.preventDefault();

        /*
         * Pour le moment, les paramètres sont locaux.
         *
         * Plus tard :
         * PUT /api/users/profile
         */

        localStorage.setItem(
            "dataviz_language",
            language
        );

        localStorage.setItem(
            "dataviz_notifications",
            notifications
        );

        setMessage(
            "Paramètres enregistrés."
        );
    };

    // ==========================================================
    // RENDER
    // ==========================================================

    return (
        <div className="page-container settings-page">

            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="page-header">

                <div>

                    <h1>
                        Paramètres
                    </h1>

                    <p>
                        Gérez votre compte et les préférences
                        de DataViz.
                    </p>

                </div>

            </div>


            {/* ==================================================
                MESSAGE
            ================================================== */}

            {message && (

                <div className="status-message">
                    {message}
                </div>

            )}


            {/* ==================================================
                PROFIL
            ================================================== */}

            <div className="card">

                <div className="card-title">

                    <div>

                        <h2>
                            Profil
                        </h2>

                        <p>
                            Informations de votre compte.
                        </p>

                    </div>

                </div>


                <form onSubmit={handleSave}>

                    <div className="form-group">

                        <label htmlFor="name">
                            Nom
                        </label>

                        <input
                            id="name"
                            type="text"
                            value={name}
                            onChange={(e) =>
                                setName(e.target.value)
                            }
                            placeholder="Votre nom"
                        />

                    </div>


                    <div className="form-group">

                        <label htmlFor="email">
                            Adresse email
                        </label>

                        <input
                            id="email"
                            type="email"
                            value={email}
                            disabled
                        />

                        <small>
                            L'adresse email ne peut pas être
                            modifiée ici.
                        </small>

                    </div>


                    <div className="form-group">

                        <label>
                            Rôle
                        </label>

                        <input
                            type="text"
                            value={
                                user?.role ||
                                "Utilisateur"
                            }
                            disabled
                        />

                    </div>


                    {/* ==================================================
                        PREFERENCES
                    ================================================== */}

                    <div className="settings-section">

                        <h2>
                            Préférences
                        </h2>


                        <div className="form-group">

                            <label htmlFor="language">
                                Langue
                            </label>

                            <select
                                id="language"
                                value={language}
                                onChange={(e) =>
                                    setLanguage(
                                        e.target.value
                                    )
                                }
                            >

                                <option value="fr">
                                    Français
                                </option>

                                <option value="en">
                                    English
                                </option>

                            </select>

                        </div>


                        <div className="settings-option">

                            <div>

                                <strong>
                                    Notifications
                                </strong>

                                <p>
                                    Recevoir les notifications
                                    de l'application.
                                </p>

                            </div>

                            <label className="switch">

                                <input
                                    type="checkbox"
                                    checked={notifications}
                                    onChange={(e) =>
                                        setNotifications(
                                            e.target.checked
                                        )
                                    }
                                />

                                <span className="slider"></span>

                            </label>

                        </div>

                    </div>


                    {/* ==================================================
                        ACTIONS
                    ================================================== */}

                    <div className="buttons-row">

                        <button
                            type="submit"
                            className="primary-btn"
                        >
                            Enregistrer
                        </button>

                    </div>

                </form>

            </div>


            {/* ==================================================
                SECURITE
            ================================================== */}

            <div className="card">

                <div className="card-title">

                    <div>

                        <h2>
                            Sécurité
                        </h2>

                        <p>
                            Gérez la sécurité de votre compte.
                        </p>

                    </div>

                </div>


                <div className="settings-action">

                    <div>

                        <strong>
                            Mot de passe
                        </strong>

                        <p>
                            Modifiez votre mot de passe
                            de connexion.
                        </p>

                    </div>

                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={() => {
                            setMessage(
                                "La modification du mot de passe sera disponible prochainement."
                            );
                        }}
                    >
                        Modifier
                    </button>

                </div>

            </div>


            {/* ==================================================
                COMPTE
            ================================================== */}

            <div className="card danger-card">

                <div className="card-title">

                    <div>

                        <h2>
                            Compte
                        </h2>

                        <p>
                            Actions concernant votre session.
                        </p>

                    </div>

                </div>


                <div className="settings-action">

                    <div>

                        <strong>
                            Déconnexion
                        </strong>

                        <p>
                            Fermer votre session DataViz.
                        </p>

                    </div>

                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={logout}
                    >
                        Déconnexion
                    </button>

                </div>

            </div>

        </div>
    );
};

export default SettingsPage;