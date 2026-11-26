#!/usr/bin/env node
/**
 * Build estático sem dependências:
 *  src/index.html + src/data/client-config.json  ->  dist/index.html
 *  Substitui {{caminho.no.json}}, gera JSON-LD (AutoRepair), injeta config e analytics.
 *  Copia src/css, src/js e public/ para dist/.
 *
 * Variáveis de ambiente opcionais: GA4_ID (ex: G-XXXXXXX), CLARITY_ID, VERCEL_ANALYTICS=1 (automático na Vercel).
 */
import { readFileSync, writeFileSync, mkdirSync, cpSync, rmSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = resolve(root, 'dist');
const cfg = JSON.parse(readFileSync(resolve(root, 'src/data/client-config.json'), 'utf8'));

const get = (path) => path.split('.').reduce((o, k) => (o == null ? o : o[k]), cfg);

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');

function jsonLd() {
    const h = cfg.hours;
    const pad = (n) => String(n).padStart(2, '0');
    const data = {
        '@context': 'https://schema.org',
        '@type': cfg.business.schemaType,
        name: cfg.site.name,
        description: cfg.site.description,
        url: cfg.site.url,
        telephone: cfg.contact.phoneE164,
        priceRange: cfg.business.priceRange,
        image: cfg.site.ogImage,
        address: {
            '@type': 'PostalAddress',
            streetAddress: cfg.address.street,
            addressLocality: cfg.address.city,
            addressRegion: cfg.address.state,
            postalCode: cfg.address.postalCode,
            addressCountry: cfg.address.country,
        },
        areaServed: cfg.business.areaServed,
        openingHoursSpecification: [
            {
                '@type': 'OpeningHoursSpecification',
                dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                opens: `${pad(h.weekdayOpen)}:00`,
                closes: `${pad(h.weekdayClose)}:00`,
            },
            {
                '@type': 'OpeningHoursSpecification',
                dayOfWeek: 'Saturday',
                opens: `${pad(h.saturdayOpen)}:00`,
                closes: `${pad(h.saturdayClose)}:00`,
            },
        ],
        aggregateRating: {
            '@type': 'AggregateRating',
            ratingValue: cfg.rating.value,
            reviewCount: String(cfg.rating.reviewCount),
            bestRating: '5',
        },
        sameAs: [cfg.contact.instagram],
    };
    return `<script type="application/ld+json">\n${JSON.stringify(data, null, 2).replace(/</g, '\\u003c')}\n    </script>`;
}

function analytics() {
    const out = [];
    const ga = process.env.GA4_ID;
    const clarity = process.env.CLARITY_ID;
    // Vercel Web Analytics (site estático): ativo no build da Vercel (VERCEL=1) ou com VERCEL_ANALYTICS=1.
    // Requer ativar "Analytics" no painel do projeto na Vercel.
    if (process.env.VERCEL === '1' || process.env.VERCEL_ANALYTICS === '1') {
        out.push(
            `<script>window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments);};</script>`,
            `<script defer src="/_vercel/insights/script.js"></script>`
        );
    }
    if (ga) {
        out.push(
            `<script async src="https://www.googletagmanager.com/gtag/js?id=${esc(ga)}"></script>`,
            `<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${esc(ga)}');</script>`
        );
    }
    if (clarity) {
        out.push(
            `<script>(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","${esc(clarity)}");</script>`
        );
    }
    return out.length ? out.join('\n    ') : '<!-- Analytics desativado: defina GA4_ID e/ou CLARITY_ID no build -->';
}


const escHtml = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function serviceCards() {
    return cfg.services
        .map(
            (sv) => `<article class="group bg-garage-card hover:bg-[#202023] border border-garage-border hover:border-garage-red/60 rounded-2xl p-6 flex flex-col justify-between transition-all duration-300">
                        <div>
                            <div class="w-12 h-12 rounded-xl bg-garage-red/15 border border-garage-red/30 text-red-400 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">${sv.iconSvg}</svg>
                            </div>
                            <h3 class="font-display font-bold text-xl text-white uppercase tracking-wide mb-2">${escHtml(sv.name)}</h3>
                            <p class="text-sm text-slate-400 leading-relaxed mb-6">${escHtml(sv.description)}</p>
                        </div>
                        <button type="button" data-open-quote data-quote-service="${escHtml(sv.name)}" class="w-full min-h-[48px] py-3 px-4 rounded-xl bg-garage-dark hover:bg-garage-red text-white border border-garage-border hover:border-garage-red font-semibold text-sm transition-colors flex items-center justify-center gap-2">
                            <span>Orçar este serviço</span>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                        </button>
                    </article>`
        )
        .join('\n\n                    ');
}

function serviceOptions() {
    const opts = [...cfg.services.map((sv) => sv.name), 'Outro serviço / Avaliação geral'];
    return opts.map((n) => `<option value="${escHtml(n)}">${escHtml(n)}</option>`).join('\n                            ');
}

let html = readFileSync(resolve(root, 'src/index.html'), 'utf8');
html = html
    .replace('{{__JSONLD__}}', () => jsonLd())
    .replace('{{__SERVICE_CARDS__}}', () => serviceCards())
    .replace('{{__SERVICE_OPTIONS__}}', () => serviceOptions())
    .replace('{{__ANALYTICS__}}', () => analytics())
    .replace('{{__CONFIG_JSON__}}', () => `<script type="application/json" id="client-config">${JSON.stringify(cfg).replace(/</g, '\\u003c')}</script>`)
    .replace(/\{\{([\w.]+)\}\}/g, (_m, p) => {
        const v = get(p);
        if (v === undefined) throw new Error(`Token sem valor no client-config.json: {{${p}}}`);
        return v;
    });

rmSync(dist, { recursive: true, force: true });
mkdirSync(resolve(dist, 'assets'), { recursive: true });
if (existsSync(resolve(root, 'public'))) cpSync(resolve(root, 'public'), dist, { recursive: true });
cpSync(resolve(root, 'src/css'), resolve(dist, 'assets/css'), { recursive: true });
cpSync(resolve(root, 'src/js'), resolve(dist, 'assets/js'), { recursive: true });
writeFileSync(resolve(dist, 'index.html'), html);

// CSS do Tailwind compilado e minificado (lê classes de src/ e deste script)
execFileSync(
    resolve(root, 'node_modules/.bin/tailwindcss'),
    ['-c', 'tailwind.config.cjs', '-i', 'src/tailwind.input.css', '-o', 'dist/assets/css/tailwind.css', '--minify'],
    { cwd: root, stdio: 'inherit' }
);
console.log(`Build OK -> ${dist} (analytics: GA4=${Boolean(process.env.GA4_ID)}, Clarity=${Boolean(process.env.CLARITY_ID)})`);
