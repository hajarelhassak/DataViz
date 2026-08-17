// src/pages/AIPage.jsx

import { useEffect, useState } from "react";
import { aiApi } from "../api/ai";

const AIPage = () => {

    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");



    useEffect(() => {

        loadReports();

    }, []);





    const loadReports = async () => {

        try {

            const response = await aiApi.getReports();

            setReports(response.data);

        }

        catch (error) {

            console.error(error);

            setMessage(
                "Impossible de charger les analyses IA."
            );

        }

        finally {

            setLoading(false);

        }

    };





    return (

        <div className="page-container ai-page">


            <div className="page-header">

                <div>

                    <h1>
                        Assistant IA
                    </h1>

                    <p>
                        Consultez les analyses générées automatiquement à partir
                        des données de vos espaces d'analyse.
                    </p>

                </div>

            </div>






            {
                message &&
                <div className="card">

                    <p className="status-message">
                        {message}
                    </p>

                </div>
            }







            {

                loading ?

                (

                    <div className="card">

                        <div className="empty-state">

                            Chargement des analyses...

                        </div>

                    </div>

                )

                :

                reports.length === 0 ?

                (

                    <div className="card">

                        <div className="empty-state">

                            <h2>
                                Aucune analyse disponible
                            </h2>

                            <p>

                                Les analyses générées par l'IA
                                apparaîtront ici après leur exécution.

                            </p>

                        </div>

                    </div>

                )

                :

                <div className="dashboard-grid">


                    {

                        reports.map((report)=>(

                            <div
                                className="card ai-report-card"
                                key={report.id}
                            >


                                <div className="card-title">

                                    <h2>

                                        Rapport IA

                                    </h2>

                                </div>





                                <div className="report-section">

                                    <strong>

                                        Statut

                                    </strong>

                                    <p>

                                        {report.statut}

                                    </p>

                                </div>






                                <div className="report-section">

                                    <strong>

                                        Résultat

                                    </strong>

                                    <p>

                                        {

                                            report.resultat?.analyse ||

                                            "Aucune analyse disponible."

                                        }

                                    </p>

                                </div>







                                <div className="report-section">

                                    <strong>

                                        Date

                                    </strong>

                                    <p>

                                        {

                                            report.created_at

                                            ?

                                            new Date(
                                                report.created_at
                                            ).toLocaleString()

                                            :

                                            "-"

                                        }

                                    </p>

                                </div>



                            </div>

                        ))

                    }



                </div>

            }




        </div>

    );

};

export default AIPage;