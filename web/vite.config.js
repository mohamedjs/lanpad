import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// server.py serves dist/ from the same origin as the input API, so no proxy and no CORS.
export default defineConfig({ plugins: [react()], base: './' });
