// src/components/common/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";


const ProtectedRoute = ({children})=>{


    const {
        isAuthenticated,
        loading
    } = useAuth();



    if(loading){

        return (
            <div className="loading-center">
                Chargement...
            </div>
        );

    }



    if(!isAuthenticated){

        return (
            <Navigate
                to="/login"
                replace
            />
        );

    }



    return children;


};



export default ProtectedRoute;