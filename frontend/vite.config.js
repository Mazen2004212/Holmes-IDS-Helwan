import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5174,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
                secure: false,
                configure: (proxy) => {
                    proxy.on('error', (err, _req, res) => {
                        const statusCode = err.code === 'ECONNREFUSED' ? 503 : 500;
                        const message = err.code === 'ECONNREFUSED'
                            ? 'Backend server is not running on http://127.0.0.1:8000'
                            : 'Backend proxy error';

                        if (!res.headersSent) {
                            res.writeHead(statusCode, { 'Content-Type': 'application/json' });
                        }
                        res.end(JSON.stringify({ success: false, error: message }));
                    });
                },
            },
        },
    },
})
