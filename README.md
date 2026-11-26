# Garage Route 66 — Landing Page (template-mãe)

Site estático da oficina **Garage Route 66** (Parelheiros - SP). Veja [ARCHITECTURE.md](ARCHITECTURE.md).

## Uso

```bash
npm install       # uma vez (Tailwind CLI)
npm run build     # gera dist/
npm run dev       # build + servidor em http://localhost:8080
npm run deploy:preview   # ver docs/dns-e-analytics.md
```

Dados do cliente: `src/data/client-config.json`. Fotos: `public/assets/fotos/`.

## Antes de publicar (pendências reais)

- [ ] Fotos reais em `public/assets/fotos/` (hoje são placeholders gerados) e usar no Hero/`og:image` (hoje imagem do Unsplash).
- [ ] Substituir os 3 depoimentos provisórios por avaliações reais do Google e usar o link oficial do perfil.
- [ ] Confirmar com o dono: telefone, horários, serviços, garantia, nota 5,0 / 43 avaliações.
- [ ] Domínio final em `client-config.json`, `public/robots.txt`, `public/sitemap.xml`.
- [ ] Definir `GA4_ID`/`CLARITY_ID` e avaliar aviso de cookies (LGPD).

## Docs do time

[arquitetura-cto](docs/arquitetura-cto.md) · [ux-spec](docs/ux-spec.md) · [infra-deploy](docs/infra-deploy.md) · [dns-e-analytics](docs/dns-e-analytics.md)

> Alguns caminhos nos docs antigos (`assets/...`, `index.html` na raiz) refletem a estrutura anterior; vale a `ARCHITECTURE.md`.
