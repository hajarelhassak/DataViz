// src/App.jsx

import {
    HashRouter,
    Routes,
    Route,
    Navigate,
} from "react-router-dom";

import {
    AuthProvider,
    useAuth,
} from "./context/AuthContext";

import {
    ProjectProvider,
} from "./context/ProjectContext";

import ProtectedRoute
    from "./components/common/ProtectedRoute";

import AppLayout
    from "./components/layout/AppLayout";

import {
    LoginPage,
    DashboardPage,
    ProjectsPage,
    ProjectDetailsPage,
    WorkspacePage,
    ConnectionsPage,
    ConnectionPage,
    SchemaPage,
    TableSelectionPage,
    CreateDashboardPage,
    DashboardViewPage,
    AIPage,
} from "./pages";

import SettingsPage
    from "./pages/SettingsPage";


function AppRoutes() {

    const { loading } = useAuth();


    if (loading) {

        return (

            <div className="loading-center">

                <div className="loading-spinner"></div>

                <p>
                    Chargement...
                </p>

            </div>
        );
    }


    return (

        <Routes>

            {/* LOGIN */}

            <Route
                path="/login"
                element={
                    <LoginPage />
                }
            />


            {/* APPLICATION */}

            <Route
                element={
                    <ProtectedRoute>
                        <AppLayout />
                    </ProtectedRoute>
                }
            >

                {/* ACCUEIL */}

                <Route
                    path="/"
                    element={
                        <DashboardPage />
                    }
                />


                {/* PROJETS */}

                <Route
                    path="/projects"
                    element={
                        <ProjectsPage />
                    }
                />

                <Route
                    path="/projects/:projectId"
                    element={
                        <ProjectDetailsPage />
                    }
                />


                {/* WORKSPACE */}

                <Route
                    path="/workspace/:projectId"
                    element={
                        <WorkspacePage />
                    }
                />


                {/* CONNEXIONS */}

                <Route
                    path="/connections/:projectId"
                    element={
                        <ConnectionsPage />
                    }
                />


                {/* NOUVELLE CONNEXION */}

                <Route
                    path="/workspace/:projectId/connection"
                    element={
                        <ConnectionPage />
                    }
                />


                {/* SCHEMA */}

                <Route
                    path="/workspace/:projectId/schema/:connectionId"
                    element={
                        <SchemaPage />
                    }
                />


                {/* TABLES */}

                <Route
                    path="/workspace/:projectId/tables/:connectionId"
                    element={
                        <TableSelectionPage />
                    }
                />


                {/* CREATION DASHBOARD */}

                <Route
                    path="/workspace/:projectId/dashboards/create"
                    element={
                        <CreateDashboardPage />
                    }
                />


                {/* DASHBOARD CREE */}

                <Route
                    path="/dashboard/:dashboardId"
                    element={
                        <DashboardViewPage />
                    }
                />


                {/* IA */}

                <Route
                    path="/ai"
                    element={
                        <AIPage />
                    }
                />


                {/* SETTINGS */}

                <Route
                    path="/settings"
                    element={
                        <SettingsPage />
                    }
                />

            </Route>


            {/* ROUTE INCONNUE */}

            <Route
                path="*"
                element={
                    <Navigate
                        to="/"
                        replace
                    />
                }
            />

        </Routes>
    );
}


function App() {

    return (

        <HashRouter>

            <AuthProvider>

                <ProjectProvider>

                    <AppRoutes />

                </ProjectProvider>

            </AuthProvider>

        </HashRouter>
    );
}


export default App;