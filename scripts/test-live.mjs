#!/usr/bin/env node
// Teste REAL da triagem (usa a chave do .env e a rede). Uso: npm run test:live
import { readFileSync, existsSync } from 'node:fs';
import { handleTriage } from '../server/triage.js';

const env = { ...process.env, DEBUG_TRIAGE: '1' };
if (existsSync('.env')) {
    for (const line of readFileSync('.env', 'utf8').split('\n')) {
        const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
        if (m && m[2]) env[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
}
console.log('Chave:', env.GEMINI_API_KEY ? `presente (${env.GEMINI_API_KEY.length} caracteres)` : 'AUSENTE');
console.log('Modelo:', env.GEMINI_MODEL || 'gemini-3.5-flash-lite (padrão)');
if (!env.GEMINI_API_KEY) { console.log('Crie o .env com GEMINI_API_KEY=... e rode de novo.'); process.exit(1); }

const config = JSON.parse(readFileSync('src/data/client-config.json', 'utf8'));
const origin = new URL(config.site.url).origin;
for (const symptom of ['Estou ouvindo um barulho na roda da frente quando freio', 'O pedal do freio foi até o fundo e o carro quase não parou']) {
    const req = new Request('http://x/api/triage', { method: 'POST', headers: { 'content-type': 'application/json', origin }, body: JSON.stringify({ symptom, vehicle: 'Onix 2019' }) });
    const res = await handleTriage(req, env, config);
    console.log('\n>', symptom, '\nHTTP', res.status, await res.text());
}
