import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: vitePreprocess(),
    kit: {
        // Static SPA: served from FastAPI as a fallback. All routes resolve
        // through index.html and call the API at the same origin.
        adapter: adapter({
            pages: 'build',
            assets: 'build',
            fallback: 'index.html',
            strict: false
        }),
        alias: {
            $lib: 'src/lib'
        }
    }
};

export default config;
