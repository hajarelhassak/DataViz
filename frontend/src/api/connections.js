// src/api/connections.js

import axios from "./axios";

export const connectionsApi = {

    // ======================================================
    // TESTER UNE CONNEXION
    // ======================================================

    test(data) {
        return axios.post("/connections/test", data);
    },


    // ======================================================
    // LISTE DES CONNEXIONS D'UN PROJET
    // ======================================================

    list(projectId) {
        return axios.get(
            `/connections/project/${projectId}`
        );
    },


    // ======================================================
    // CREER UNE CONNEXION
    // ======================================================

    create(projectId, data) {
        return axios.post(
            `/connections/project/${projectId}`,
            data
        );
    },


    // ======================================================
    // EXPLORER LE SCHEMA
    // ======================================================

    explore(connectionId) {
        return axios.post(
            `/connections/${connectionId}/explore`
        );
    },


    // ======================================================
    // RECUPERER LE SCHEMA
    // ======================================================

    schema(connectionId) {
        return axios.get(
            `/connections/${connectionId}/schema`
        );
    },


    // ======================================================
    // TABLES SELECTIONNEES
    // ======================================================

    saveTables(connectionId, tables) {

        const selectedTables =
            Array.isArray(tables)
                ? tables
                : Array.isArray(tables?.tables)
                    ? tables.tables
                    : [];

        return axios.post(
            `/connections/${connectionId}/tables`,
            {
                tables: selectedTables,
            }
        );
    },


    // ======================================================
    // ANALYSE IA
    // ======================================================

    analyze(connectionId) {
        return axios.post(
            `/connections/${connectionId}/analyze`
        );
    },


    // ======================================================
    // RETEST
    // ======================================================

    retest(connectionId) {
        return axios.post(
            `/connections/${connectionId}/retest`
        );
    },


    // ======================================================
    // SUPPRIMER UNE CONNEXION
    // ======================================================

    delete(connectionId) {
        return axios.delete(
            `/connections/${connectionId}`
        );
    },
};