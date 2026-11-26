# DNS, Deploy e Analytics

## Deploy da demo (`garageroute66-demo`)

```bash
cp .env.example .env        # defina DEPLOY_PROVIDER (netlify|vercel|cloudflare) e, opcional, GA4_ID/CLARITY_ID
npm run deploy:preview      # link de preview
npm run deploy:prod         # produção
```

Na primeira execução o CLI pede login no navegador (`netlify login`, `vercel login` ou `wrangler login`). Isso exige conta do dono/agência; **o preview ainda não foi publicado**.

## Apontar o domínio .com.br

Registre em registro.br e escolha **uma** das opções:

**A) Nameservers (recomendado com Cloudflare):** no Registro.br, troque os DNS pelos dois nameservers que o Cloudflare indicar. O resto é gerenciado lá.

**B) Registros manuais (DNS do Registro.br ou outro):**

| Tipo | Nome | Valor |
|---|---|---|
| A | `@` | IP indicado pelo provedor (Netlify: `75.2.60.5`; Vercel: `76.76.21.21`) — confirme no painel antes |
| CNAME | `www` | Netlify: `garageroute66-demo.netlify.app` · Vercel: `cname.vercel-dns.com` · Cloudflare Pages: `garageroute66-demo.pages.dev` |

Cloudflare Pages não usa registro A para domínio raiz fora do Cloudflare DNS; nesse caso use a opção A. Depois: adicionar o domínio no painel do provedor, aguardar o SSL automático (minutos a 24h) e atualizar `site.url` em `src/data/client-config.json`, `public/robots.txt` e `public/sitemap.xml`.

## Analytics (relatório mensal)

- **GA4:** crie a propriedade, copie o ID `G-XXXXXXX` para `GA4_ID` e rode o deploy. Marque como conversão o evento `whatsapp_click` (Admin → Eventos). Relatório mensal: Relatórios → Engajamento → Eventos, filtrando por `service_name`.
- **Microsoft Clarity:** gratuito, mapa de calor e gravações; defina `CLARITY_ID`.
- **Vercel Web Analytics:** não use `npm i @vercel/analytics` (esse pacote é para Next.js). Aqui o build injeta o script `/_vercel/insights/script.js` sozinho quando roda na Vercel. Falta só ativar **Analytics** no painel do projeto (aba Analytics → Enable) e fazer um novo deploy. Os eventos do site também vão para a Vercel via `va('event', ...)`; eventos personalizados podem depender do plano (confira na Vercel). Só funciona no domínio hospedado lá, não no `localhost`.
- Sem as variáveis, nenhum script de analytics é carregado (o build deixa um comentário no HTML).
- Eventos enviados: `whatsapp_click`, `telefone_click`, `rota_maps_click`, `waze_click`, `instagram_click`.
- Aviso: o site não tem banner de cookies/LGPD. Confirme a necessidade com o dono antes de ativar analytics em produção.
