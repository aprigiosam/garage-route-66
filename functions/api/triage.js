// Cloudflare Pages Function: POST /api/triage
// Segredo: `npx wrangler pages secret put GEMINI_API_KEY --project-name garageroute66-demo`
import config from '../../src/data/client-config.json';
import { handleTriage } from '../../server/triage.js';

export const onRequest = ({ request, env }) => handleTriage(request, env, config);
