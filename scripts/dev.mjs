#!/usr/bin/env node
/**
 * Servidor local: serve dist/ e POST /api/triage (mesma lógica da Function em produção).
 * Lê .env (GEMINI_API_KEY, GEMINI_MODEL). Uso: node scripts/dev.mjs [porta]
 */
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { resolve, dirname, extname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { handleTriage } from '../server/triage.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = resolve(root, 'dist');
const port = Number(process.argv[2] || 8080);

const env = { ...process.env };
const envFile = resolve(root, '.env');
if (existsSync(envFile)) {
    for (const line of readFileSync(envFile, 'utf8').split('\n')) {
        const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
        if (m && m[2] && !(m[1] in env && env[m[1]])) env[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
}
env.ALLOWED_ORIGINS = [env.ALLOWED_ORIGINS, `http://localhost:${port}`, `http://127.0.0.1:${port}`].filter(Boolean).join(',');

const config = JSON.parse(readFileSync(resolve(root, 'src/data/client-config.json'), 'utf8'));
const types = {
    '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
    '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.txt': 'text/plain', '.xml': 'application/xml',
};

createServer(async (req, res) => {
    const url = new URL(req.url, `http://localhost:${port}`);
    if (url.pathname === '/api/triage') {
        const chunks = [];
        for await (const c of req) chunks.push(c);
        const request = new Request(url, { method: req.method, headers: req.headers, body: ['GET', 'HEAD'].includes(req.method) ? undefined : Buffer.concat(chunks) });
        const r = await handleTriage(request, env, config);
        res.writeHead(r.status, Object.fromEntries(r.headers));
        return res.end(await r.text());
    }
    let file = normalize(resolve(dist, '.' + (url.pathname === '/' ? '/index.html' : decodeURIComponent(url.pathname))));
    if (!file.startsWith(dist) || !existsSync(file) || statSync(file).isDirectory()) {
        res.writeHead(404, { 'content-type': 'text/plain' });
        return res.end('Not found');
    }
    res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream' });
    res.end(readFileSync(file));
}).listen(port, () => console.log(`Dev server: http://localhost:${port}  (IA: ${env.GEMINI_API_KEY ? 'chave carregada' : 'SEM chave — defina GEMINI_API_KEY no .env'})`));
