# ARCHITECTURE — Template-mãe para comércios locais

Primeiro uso: **Garage Route 66** (Parelheiros - SP). Site estático, sem framework, sem dependências npm. Layout e dados separados: para um novo cliente, troque o JSON, as fotos e (se preciso) os textos do HTML.

## Estrutura

```text
garageroute66/
├── src/
│   ├── index.html                 # Template (tokens {{caminho.json}})
│   ├── tailwind.input.css         # Entrada do Tailwind (compilado no build)
│   ├── data/client-config.json    # ÚNICA fonte de dados do cliente
│   ├── css/styles.css             # Foco acessível, safe-area, reduced-motion
│   └── js/
│       ├── main.js                # UI: menu, modal, toast, horário, copiar endereço
│       └── tracking.js            # trackEvent + openTrackedWhatsApp
├── public/                        # Copiado como está para dist/
│   ├── assets/fotos/              # fachada.jpg, oficina-1.jpg, oficina-2.jpg (PLACEHOLDERS)
│   ├── assets/icons/favicon.svg
│   ├── robots.txt, sitemap.xml, _headers
├── scripts/
│   ├── build.mjs                  # Gera dist/ (JSON-LD, config, analytics)
│   └── deploy.sh                  # Netlify | Vercel | Cloudflare Pages
├── docs/                          # Specs do time + dns-e-analytics.md
├── tailwind.config.cjs            # Tema (cores da fachada) e arquivos varridos
├── netlify.toml, vercel.json, .env.example
└── dist/                          # Gerado (não versionado)
```

## Fluxo de build

`src/index.html` + `client-config.json` → `node scripts/build.mjs` → `dist/index.html`.
O build: substitui tokens (falha se faltar chave), gera o **JSON-LD `AutoRepair`** (endereço, CEP, horários, `aggregateRating`), injeta o JSON em `<script id="client-config">` (lido pelo JS) gera os cards de serviço e as `<option>` do formulário a partir de `services`, compila o **Tailwind** em `dist/assets/css/tailwind.css` (~27 KB minificado) e injeta GA4/Clarity se `GA4_ID`/`CLARITY_ID` estiverem definidos.

## Template-mãe: novo cliente

1. Copiar o repositório.
2. Editar `src/data/client-config.json` (nome, telefone, endereço, horários, nota, serviços, URL).
3. Trocar fotos em `public/assets/fotos/` e textos/serviços em `src/index.html`.
4. `npm run build` e deploy.

Os **serviços** (nome, descrição, ícone) vêm de `client-config.json`. Textos de marketing (Hero, diferenciais, depoimentos) ainda estão no HTML.

## Rastreamento de leads

- Toda mensagem de WhatsApp começa com **`[Site Oficial]`** (`site.trackingTag`), permitindo ao dono filtrar leads vindos do site.
- `openTrackedWhatsApp(serviceName, vehicleInfo, extra)` monta a mensagem, chama `trackEvent('whatsapp_click', {service_name, has_vehicle_info, source})` e abre `wa.me/<número>`.
- `trackEvent` envia para `dataLayer`, `gtag` (GA4), `clarity` e contador em `localStorage` (`gr66_leads`: total, por evento, serviço e dia — só no navegador do visitante, serve de debug).
- Outros eventos (`data-track`): `telefone_click`, `rota_maps_click`, `waze_click`, `instagram_click`.
- `source` identifica a origem: `modal_orcamento`, `link_direto` ou o valor de `data-track-source`.

## SEO local

JSON-LD `AutoRepair` com `aggregateRating` (5.0 / 43), `areaServed`, horários e `sameAs`. Mantenha nota e contagem em `client-config.json` iguais ao perfil do Google; dado desatualizado no schema pode gerar penalidade.

## Decisões e pendências

- Tailwind v3 compilado via CLI (única devDependency; precisa de `npm install` uma vez). O CDN foi removido e a CSP não usa mais `unsafe-eval`.
- Foto do Hero e depoimentos ainda são **provisórios** (ver README).
