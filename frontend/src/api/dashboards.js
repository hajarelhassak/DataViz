import axios from "./axios";


export const dashboardsApi = {


    create(data){

        return axios.post(
            "/dashboards",
            data
        );

    },


    list(projectId){

        return axios.get(
            `/projects/${projectId}/dashboards`
        );

    },


    get(id){

        return axios.get(
            `/dashboards/${id}`
        );

    },


    generate(data){

        return axios.post(
            "/dashboards/generate",
            data
        );

    }

};