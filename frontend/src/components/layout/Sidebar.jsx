// src/components/layout/Sidebar.jsx

import { NavLink } from "react-router-dom";

import { useProject } from "../../context/ProjectContext";

const Sidebar = () => {

    const {
        currentProject,
        projectLoading,
    } = useProject();

    const projectId =
        currentProject?.id;


    const mainMenu = [
        {
            label: "Vue générale",
            path: "/",
            icon: "⌂",
        },
        {
            label: "Mes projets",
            path: "/projects",
            icon: "▦",
        },
    ];


    return (
        <aside className="sidebar">

            {/* ==================================================
                LOGO
            ================================================== */}

            <div className="sidebar-logo">

                <div className="logo-box">
                    DV
                </div>

                <div>
                    <h2>DataViz</h2>

                    <span>
                        Intelligence Platform
                    </span>
                </div>

            </div>


            {/* ==================================================
                NAVIGATION
            ================================================== */}

            <nav className="sidebar-menu">

                {/* ==================================================
                    MENU PRINCIPAL
                ================================================== */}

                {mainMenu.map((item) => (

                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === "/"}
                        className={({ isActive }) =>
                            isActive
                                ? "menu-item active"
                                : "menu-item"
                        }
                    >

                        <span className="menu-icon">
                            {item.icon}
                        </span>

                        <span>
                            {item.label}
                        </span>

                    </NavLink>

                ))}


                {/* ==================================================
                    PROJET ACTIF
                ================================================== */}

                <div className="sidebar-section-title">
                    PROJET ACTIF
                </div>


                {projectLoading ? (

                    <div className="sidebar-hint">
                        Chargement du projet...
                    </div>

                ) : projectId ? (

                    <>

                        {/* NOM */}

                        <div className="active-project">

                            <span className="sidebar-status-dot"></span>

                            <span>
                                {currentProject?.nom ||
                                    currentProject?.name ||
                                    `Projet ${projectId}`}
                            </span>

                        </div>


                        {/* WORKSPACE */}

                        <NavLink
                            to={`/workspace/${projectId}`}
                            className={({ isActive }) =>
                                isActive
                                    ? "menu-item active"
                                    : "menu-item"
                            }
                        >

                            <span className="menu-icon">
                                ◈
                            </span>

                            <span>
                                Workspace
                            </span>

                        </NavLink>


                        {/* CONNEXIONS */}

                        <NavLink
                            to={`/connections/${projectId}`}
                            className={({ isActive }) =>
                                isActive
                                    ? "menu-item active"
                                    : "menu-item"
                            }
                        >

                            <span className="menu-icon">
                                ◉
                            </span>

                            <span>
                                Connexions BDD
                            </span>

                        </NavLink>


                        {/* DASHBOARDS */}

                        <NavLink
                            to={`/projects/${projectId}`}
                            className={({ isActive }) =>
                                isActive
                                    ? "menu-item active"
                                    : "menu-item"
                            }
                        >

                            <span className="menu-icon">
                                ▣
                            </span>

                            <span>
                                Dashboards
                            </span>

                        </NavLink>

                    </>

                ) : (

                    <div className="sidebar-hint">

                        Sélectionnez un projet pour
                        accéder à son espace.

                    </div>

                )}


                {/* ==================================================
                    OUTILS
                ================================================== */}

                <div className="sidebar-section-title">
                    OUTILS
                </div>


                {/* IA */}

                <NavLink
                    to="/ai"
                    className={({ isActive }) =>
                        isActive
                            ? "menu-item active"
                            : "menu-item"
                    }
                >

                    <span className="menu-icon">
                        ✦
                    </span>

                    <span>
                        Assistant IA
                    </span>

                </NavLink>

            </nav>


            {/* ==================================================
                FOOTER
            ================================================== */}

            <div className="sidebar-footer">

                <div className="sidebar-project-status">

                    <span
                        className={
                            projectId
                                ? "sidebar-status-dot"
                                : "sidebar-status-dot inactive"
                        }
                    ></span>

                    <span>
                        {projectId
                            ? "Projet actif"
                            : "Aucun projet actif"}
                    </span>

                </div>

                <p>
                    DataViz · v1.0
                </p>

            </div>

        </aside>
    );
};

export default Sidebar;