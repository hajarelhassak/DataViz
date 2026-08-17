// src/context/ProjectContext.jsx

import {
    createContext,
    useContext,
    useState,
    useEffect,
    useCallback,
} from "react";

const ProjectContext = createContext(null);

// ==========================================================
// PROVIDER
// ==========================================================

export const ProjectProvider = ({ children }) => {

    const [currentProject, setCurrentProject] =
        useState(null);

    const [projectLoading, setProjectLoading] =
        useState(true);


    // ======================================================
    // RESTAURER LE PROJET ACTIF
    // ======================================================

    useEffect(() => {

        const restoreProject = async () => {

            const savedId =
                localStorage.getItem(
                    "current_project_id"
                );

            // Aucun projet sauvegardé
            if (!savedId) {

                setCurrentProject(null);
                setProjectLoading(false);

                return;
            }


            const token =
                localStorage.getItem("token");


            // ==================================================
            // PAS DE TOKEN
            // ==================================================

            if (!token) {

                setCurrentProject({
                    id: savedId,
                    nom: `Projet ${savedId}`,
                });

                setProjectLoading(false);

                return;
            }


            // ==================================================
            // RECUPERATION DU PROJET
            // ==================================================

            try {

                const response = await fetch(
                    `/api/projects/${savedId}`,
                    {
                        method: "GET",

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


                if (!response.ok) {

                    throw new Error(
                        `Erreur HTTP ${response.status}`
                    );

                }


                if (
                    !contentType.includes(
                        "application/json"
                    )
                ) {

                    throw new Error(
                        "Réponse serveur non JSON"
                    );

                }


                const data =
                    await response.json();


                const project =
                    data.project ||
                    data.data ||
                    data;


                if (
                    !project ||
                    !project.id
                ) {

                    throw new Error(
                        "Projet invalide"
                    );

                }


                setCurrentProject(project);


            } catch (error) {

                console.warn(
                    "Impossible de restaurer le projet actif :",
                    error
                );


                // ==================================================
                // FALLBACK TEMPORAIRE
                // ==================================================

                setCurrentProject({
                    id: savedId,
                    nom: `Projet ${savedId}`,
                });

            } finally {

                setProjectLoading(false);

            }

        };


        restoreProject();

    }, []);


    // ======================================================
    // SELECTIONNER UN PROJET
    // ======================================================

    const selectProject = useCallback(
        (project) => {

            if (!project || !project.id) {

                setCurrentProject(null);

                localStorage.removeItem(
                    "current_project_id"
                );

                return;
            }


            setCurrentProject(project);


            localStorage.setItem(
                "current_project_id",
                String(project.id)
            );

        },
        []
    );


    // ======================================================
    // DESELECTIONNER LE PROJET
    // ======================================================

    const clearProject = useCallback(() => {

        setCurrentProject(null);

        localStorage.removeItem(
            "current_project_id"
        );

    }, []);


    // ======================================================
    // CONTEXT
    // ======================================================

    return (
        <ProjectContext.Provider
            value={{
                currentProject,
                selectProject,
                clearProject,
                projectLoading,
            }}
        >

            {children}

        </ProjectContext.Provider>
    );

};


// ==========================================================
// HOOK
// ==========================================================

export const useProject = () => {

    const context =
        useContext(ProjectContext);


    if (!context) {

        throw new Error(
            "useProject must be used within ProjectProvider"
        );

    }


    return context;

};