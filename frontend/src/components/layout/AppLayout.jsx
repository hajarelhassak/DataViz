// src/components/layout/AppLayout.jsx

import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";


const AppLayout = () => {


    return (

        <div className="app-layout">


            <Sidebar />


            <div className="main-wrapper">


                <Navbar />


                <main className="page-content">

                    <Outlet />

                </main>


            </div>


        </div>

    );

};


export default AppLayout;