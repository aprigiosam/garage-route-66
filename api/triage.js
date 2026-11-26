// Vercel Function: POST /api/triage
// Variáveis (Vercel -> Settings -> Environment Variables): GEMINI_API_KEY, opcional GEMINI_MODEL e ALLOWED_ORIGINS.
import config from '../src/data/client-config.json' with { type: 'json' };
import { handleTriage } from '../server/triage.js';

export async function POST(request) {
    // Libera automaticamente os domínios da própria Vercel (produção e preview).
    const vercelOrigins = [process.env.VERCEL_PROJECT_PRODUCTION_URL, process.env.VERCEL_URL]
        .filter(Boolean)
        .map((host) => `https://${host}`);
    const env = {
        ...process.env,
        ALLOWED_ORIGINS: [process.env.ALLOWED_ORIGINS, ...vercelOrigins].filter(Boolean).join(','),
    };
    return handleTriage(request, env, config);
}

// Outros métodos recebem 405 do mesmo handler.
export const GET = POST;
export const PUT = POST;
export const DELETE = POST;
