// src/components/layout/Navbar.jsx

import { useState } from "react";
import {
    useLocation,
    useNavigate,
} from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

const Navbar = () => {

    const { user, logout } = useAuth();

    const navigate = useNavigate();

    const location = useLocation();

    const [isDropdownOpen, setIsDropdownOpen] =
        useState(false);


    // ==========================================================
    // TITRE DYNAMIQUE
    // ==========================================================

    const getPageTitle = () => {

        const path = location.pathname;

        if (path === "/") {
            return "Vue générale";
        }

        if (path === "/projects") {
            return "Mes projets";
        }

        if (path.startsWith("/projects/")) {
            return "Consultation du projet";
        }

        if (path.startsWith("/workspace/")) {
            return "Workspace";
        }

        if (path.startsWith("/connections/")) {
            return "Connexions BDD";
        }

        if (path.startsWith("/schema/")) {
            return "Exploration du schéma";
        }

        if (path === "/ai") {
            return "Assistant IA";
        }

        if (path === "/settings") {
            return "Paramètres";
        }

        return "DataViz AI Connector";
    };


    // ==========================================================
    // INITIAL USER
    // ==========================================================

    const userName =
        user?.name ||
        user?.username ||
        "Utilisateur";

    const userEmail =
        user?.email ||
        "";

    const userRole =
        user?.role ||
        "Utilisateur";

    const userInitial =
        userName
            .charAt(0)
            .toUpperCase();


    // ==========================================================
    // LOGOUT
    // ==========================================================

    const handleLogout = () => {

        setIsDropdownOpen(false);

        logout();
    };


    // ==========================================================
    // RENDER
    // ==========================================================

    return (

        <header className="navbar">

            {/* ==================================================
                GAUCHE
            ================================================== */}

            <div className="navbar-left">

                <div className="navbar-breadcrumb">

                    <span className="breadcrumb-item">
                        {getPageTitle()}
                    </span>

                </div>

            </div>


            {/* ==================================================
                DROITE
            ================================================== */}

            <div className="navbar-right">


                {/* ==================================================
                    RECHERCHE
                ================================================== */}

                <div className="search-wrapper">

                    <input
                        type="text"
                        placeholder="Rechercher..."
                        className="search-input"
                    />

                </div>


                {/* ==================================================
                    PROFIL
                ================================================== */}

                <div className="user-profile">


                    {/* AVATAR */}

                    <button
                        type="button"
                        className="user-avatar"
                        onClick={() =>
                            setIsDropdownOpen(
                                !isDropdownOpen
                            )
                        }
                    >
                        {userInitial}
                    </button>


                    {/* INFORMATIONS */}

                    <div className="user-info">

                        <strong>
                            {userName}
                        </strong>

                        <span>
                            {userRole}
                        </span>

                    </div>


                    {/* ==================================================
                        DROPDOWN
                    ================================================== */}

                    {isDropdownOpen && (

                        <div className="dropdown-menu">


                            {/* HEADER */}

                            <div className="dropdown-header">

                                <strong>
                                    {userName}
                                </strong>

                                <span>
                                    {userEmail}
                                </span>

                            </div>


                            <div className="dropdown-divider" />


                            {/* PROFIL */}

                            <button
                                type="button"
                                className="dropdown-item"
                                onClick={() => {

                                    setIsDropdownOpen(false);

                                    navigate("/profile");

                                }}
                            >
                                <span>
                                    👤
                                </span>

                                Mon profil

                            </button>


                            {/* PARAMETRES */}

                            <button
                                type="button"
                                className="dropdown-item"
                                onClick={() => {

                                    setIsDropdownOpen(false);

                                    navigate("/settings");

                                }}
                            >

                                <span>
                                    ⚙
                                </span>

                                Paramètres

                            </button>


                            {/* AIDE */}

                            <button
                                type="button"
                                className="dropdown-item"
                                onClick={() => {

                                    setIsDropdownOpen(false);

                                }}
                            >

                                <span>
                                    ?
                                </span>

                                Aide

                            </button>


                            <div className="dropdown-divider" />


                            {/* DECONNEXION */}

                            <button
                                type="button"
                                className="dropdown-item logout-item"
                                onClick={handleLogout}
                            >

                                <span>
                                    ↪
                                </span>

                                Déconnexion

                            </button>

                        </div>

                    )}

                </div>

            </div>

        </header>

    );
};

export default Navbar;