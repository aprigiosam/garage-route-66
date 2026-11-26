# IA no site: triagem de sintomas

No modal de pré-orçamento, o botão **"Não sei o serviço: sugerir com IA"** lê o relato do cliente, escolhe um dos serviços cadastrados e mostra uma mensagem curta. O cliente continua livre para trocar o serviço. Se a IA falhar, o formulário funciona normalmente.

## Como funciona

```text
Navegador  ->  POST /api/triage  ->  Function (guarda a chave)  ->  Gemini
```

- Lógica em [server/triage.js](../server/triage.js). Em produção roda como Vercel Function ([api/triage.js](../api/triage.js)) ou Cloudflare Pages Function ([functions/api/triage.js](../functions/api/triage.js)). Localmente roda em `scripts/dev.mjs`.
- A resposta é limitada por esquema: o serviço só pode ser um dos de `client-config.json` (ou "Outro serviço"), e o servidor valida de novo.
- O prompt proíbe preço, prazo e diagnóstico definitivo, e marca risco (freio, superaquecimento, fumaça) como **urgente**.
- Proteções: só aceita a origem do site, relato entre 5 e 400 caracteres, corpo máximo de 2 KB, 8 requisições por IP a cada 10 min (por instância da Function; é uma trava simples, não um limite exato), timeout de 9 s. Os logs não guardam o texto do cliente.
- Desligar: `"ai": { "enabled": false }` em `client-config.json`.

## Ativar localmente

1. `cp .env.example .env` e preencha `GEMINI_API_KEY=` (o `.env` não vai para o Git).
2. `npm run dev` e abra http://localhost:8080. O terminal mostra "chave carregada".
3. `npm test` roda os testes da função com chamadas simuladas (não usa a chave).

## Ativar em produção (Cloudflare Pages)

```bash
npx wrangler pages secret put GEMINI_API_KEY --project-name garageroute66-demo
```

Depois, faça o deploy normalmente (`npm run deploy:preview` com `DEPLOY_PROVIDER=cloudflare`). Adicione a URL do preview em `ALLOWED_ORIGINS` se for testar nela (ex.: `https://garageroute66-demo.pages.dev`).

## Ativar na Vercel

O adaptador é [api/triage.js](../api/triage.js). Na Vercel:

1. Projeto → **Settings → Environment Variables**: crie `GEMINI_API_KEY` (marque Production e Preview; deixe como sensível). Opcional: `GEMINI_MODEL`.
2. Se usar um domínio próprio (ex.: `garageroute66.com.br`), ele já é aceito porque está em `site.url`. Outros domínios vão em `ALLOWED_ORIGINS`. Os domínios `.vercel.app` do projeto são liberados automaticamente.
3. Faça um novo deploy (variáveis só valem para deploys feitos depois de criadas).
4. Teste no link de produção/preview: no modal, escreva um sintoma e clique em "sugerir com IA".

Pontos de atenção na Vercel:
- O limite de requisições por IP é por instância da função, então é uma trava aproximada. Para controle forte, use o Vercel Firewall (Rate Limiting) na rota `/api/triage`.
- A função usa o Node.js da Vercel. Se o deploy reclamar do `import ... with { type: 'json' }`, selecione Node 22 ou superior em Settings → General.
- O adaptador foi testado só localmente (origem, método, chave ausente), **não em um deploy real**.

> Netlify **não** executa essas funções como estão. Lá o botão mostra "indisponível".

## Cuidados

- **Modelo:** o padrão é `gemini-3.5-flash-lite` (variável `GEMINI_MODEL`). Confira no Google AI Studio se o nome ainda é válido e quais são os limites gratuitos atuais.
- **Privacidade (LGPD):** o relato do cliente é enviado ao Google. Verifique os termos do plano gratuito sobre uso dos dados e inclua um aviso de privacidade no site antes de publicar.
- **Custo:** defina um teto de gasto se ativar cobrança. O limite por IP reduz abuso, mas não substitui isso.
- **Chave exposta:** se a chave aparecer em um commit, print ou conversa, revogue e crie outra no AI Studio.
