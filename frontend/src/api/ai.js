import axios from "./axios";


export const aiApi = {


    getReports(){

        return axios.get(
            "/ai/reports"
        );

    },


    generate(data){

        return axios.post(
            "/ai/analyze",
            data
        );

    }


};