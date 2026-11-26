#!/usr/bin/env node
// Testes da função de triagem com fetch simulado (não chama a API real nem usa chave de verdade).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { handleTriage, resetRateLimit } from '../server/triage.js';

const config = JSON.parse(readFileSync(new URL('../src/data/client-config.json', import.meta.url), 'utf8'));
const ORIGIN = new URL(config.site.url).origin;
const env = { GEMINI_API_KEY: 'chave-de-teste' };
const realFetch = globalThis.fetch;

const req = (body, { method = 'POST', origin = ORIGIN, ip = '1.1.1.1', raw } = {}) =>
    new Request('http://x/api/triage', {
        method,
        headers: { 'content-type': 'application/json', ...(origin ? { origin } : {}), 'x-forwarded-for': ip },
        body: method === 'GET' ? undefined : raw ?? JSON.stringify(body),
    });
const gemini = (obj, status = 200) => async () => new Response(JSON.stringify({ candidates: [{ content: { parts: [{ text: typeof obj === 'string' ? obj : JSON.stringify(obj) }] } }] }), { status });
const run = async (name, fn) => { resetRateLimit(); await fn(); console.log('ok  ', name); };
const call = (r, e = env) => handleTriage(r, e, config);

await run('método GET -> 405', async () => assert.equal((await call(req(null, { method: 'GET' }))).status, 405));
await run('origem inválida -> 403', async () => assert.equal((await call(req({ symptom: 'barulho ao frear' }, { origin: 'https://evil.com' }))).status, 403));
await run('sem origem -> 403', async () => assert.equal((await call(req({ symptom: 'barulho ao frear' }, { origin: null }))).status, 403));
await run('JSON inválido -> 400', async () => assert.equal((await call(req(null, { raw: '{oops' }))).status, 400));
await run('relato curto -> 400', async () => assert.equal((await call(req({ symptom: 'oi' }))).status, 400));
await run('relato longo -> 400', async () => assert.equal((await call(req({ symptom: 'a'.repeat(401) }))).status, 400));
await run('corpo grande -> 413', async () => assert.equal((await call(req(null, { raw: 'x'.repeat(2500) }))).status, 413));
await run('sem chave -> 503', async () => assert.equal((await call(req({ symptom: 'barulho ao frear' }), {})).status, 503));

await run('sucesso e envio da chave só no header', async () => {
    let seen;
    globalThis.fetch = async (url, init) => { seen = { url, init }; return gemini({ service: 'Sistema de Freios e Suspensão', urgency: 'atencao', message: 'Precisa avaliar.' })(); };
    const res = await call(req({ symptom: 'barulho ao frear', vehicle: 'Onix 2019' }));
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { service: 'Sistema de Freios e Suspensão', urgency: 'atencao', message: 'Precisa avaliar.' });
    assert.equal(seen.init.headers['x-goog-api-key'], 'chave-de-teste');
    assert.ok(!String(seen.url).includes('chave-de-teste'));
    assert.ok(JSON.parse(seen.init.body).contents[0].parts[0].text.includes('Onix 2019'));
});
await run('serviço inventado pelo modelo -> fallback', async () => {
    globalThis.fetch = gemini({ service: 'Pintura', urgency: 'x', message: 'ok' });
    const out = await (await call(req({ symptom: 'barulho ao frear' }))).json();
    assert.equal(out.service, 'Outro serviço / Avaliação geral'); assert.equal(out.urgency, 'normal');
});
await run('upstream 500 -> 502', async () => { globalThis.fetch = gemini({}, 500); assert.equal((await call(req({ symptom: 'barulho ao frear' }))).status, 502); });
await run('resposta não-JSON -> 502', async () => { globalThis.fetch = gemini('texto solto'); assert.equal((await call(req({ symptom: 'barulho ao frear' }))).status, 502); });
await run('rate limit -> 429 na 9ª', async () => {
    globalThis.fetch = gemini({ service: 'Troca de Óleo e Filtros', urgency: 'normal', message: 'ok' });
    let last; for (let i = 0; i < 9; i++) last = await call(req({ symptom: 'trocar o óleo' }, { ip: '9.9.9.9' }));
    assert.equal(last.status, 429);
});

globalThis.fetch = realFetch;
console.log('\nTodos os testes passaram.');
