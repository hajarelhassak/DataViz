import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({

    plugins: [
        react()
    ],

    server: {

        host: "localhost",

        port: 5174,

        strictPort: true,

        proxy: {

            "/api": {

                target: "http://127.0.0.1:5000",

                changeOrigin: true,

                secure: false,

                timeout: 120000,

                proxyTimeout: 120000,
            },
        },
    },

    preview: {

        host: "localhost",

        port: 5174,

        strictPort: true,
    },
});