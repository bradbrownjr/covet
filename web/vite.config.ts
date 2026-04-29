import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        port: 5173,
        proxy: {
            // Forward API calls to the local FastAPI server during dev so the
            // browser sees a single origin (no CORS, no cookie weirdness).
            '/auth':       { target: 'http://localhost:8080', changeOrigin: true },
            '/collections':{ target: 'http://localhost:8080', changeOrigin: true },
            '/items':      { target: 'http://localhost:8080', changeOrigin: true },
            '/tags':       { target: 'http://localhost:8080', changeOrigin: true },
            '/contacts':   { target: 'http://localhost:8080', changeOrigin: true },
            '/loans':      { target: 'http://localhost:8080', changeOrigin: true },
            '/imports':    { target: 'http://localhost:8080', changeOrigin: true },
            '/healthz':    { target: 'http://localhost:8080', changeOrigin: true },
            '/version':    { target: 'http://localhost:8080', changeOrigin: true },
            '/config':     { target: 'http://localhost:8080', changeOrigin: true }
        }
    }
});
