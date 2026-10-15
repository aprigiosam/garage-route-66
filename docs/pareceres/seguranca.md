# Parecer de segurança — repo atual (React + Express/tRPC + MySQL/Drizzle, gerado pelo Manus)

- Autor: agente `seguranca` · Data: 2026-10-15 · Fase: DECISÃO (só análise, nada foi alterado no código)
- Escopo: working tree + histórico git completo (52 commits, `--all`), dependências (`pnpm-lock.yaml`), configuração e cenário operacional.

## Recomendação

1. **Ação urgente (hoje, independe da decisão de arquitetura):** rotacionar/encerrar a credencial do Postgres no Supabase que está no histórico público do GitHub (C1).
2. **Não reaproveitar a camada de autenticação nem o "andaime" Manus** (OAuth, runtime, analytics, forge). Hoje qualquer pessoa com conta Manus vira usuária com acesso total aos dados (C2). Se o código for reaproveitado, só o modelo de dados e as telas são aproveitáveis; auth, dependências e build precisam ser refeitos.
3. Em qualquer opção (reaproveitar, open source, reescrever): login local com senha forte para 1 usuária, nada exposto diretamente à internet, disco cifrado no notebook e backup cifrado fora dele.

## Premissas e verificação

- **Repo é público**: confirmado via API anônima do GitHub (`GET api.github.com/repos/aprigiosam/GarageRoute66` → `"visibility": "public"`, criado em 2025-09-26, 0 forks visíveis). Tudo no histórico deve ser tratado como vazado; forks/clones/caches de terceiros (ex.: scanners de segredos que varrem o GitHub) não podem ser descartados.
- Não testei se a credencial ainda funciona nem se os serviços Render/Supabase ainda existem (fora do escopo; não acesso infra de terceiros). Premissa: **está válida até prova em contrário**.
- `gitleaks`/`trufflehog` não estão instalados; a varredura foi feita com regex sobre `git log -p --all` (excluindo `node_modules`, `dist`, lockfile) + busca por strings de alta entropia + `git log --diff-filter=D`.
- `pnpm audit` (pnpm 10.4.1, online, sem alterar arquivos — `git status` igual antes/depois).

---

## Achados

### CRÍTICA

**C1. Senha do banco Postgres (Supabase) em texto claro no histórico público — REVOGAR JÁ**
- Tipo: connection string `postgresql://postgres.<ref>:<senha>@aws-1-us-east-1.pooler.supabase.com:5432/postgres`
  - projeto (ref): `rbxt…ewyth`; senha: `VH…Ci` (16 caracteres)
- Local: `render.yaml`, adicionado no commit `d4369cfe` (2025-10-28 13:11, "Configurações para deploy no Render e Supabase"), removido do working tree em `3f80c757` (2025-10-28 16:08) — **continua no histórico** e no GitHub público há ~1 ano.
- Agravante: commit `d0048a0b` (2025-10-28 01:34) publicou uma view **sem login na rota `/`** que imprimia `DATABASE_URL` em HTML ("Debug DATABASE_URL"); revertida em `9c0ff058` 15 min depois. Se esteve no ar no Render, a URL do banco foi exibida publicamente.
- Evidência: `git log --all -S 'pooler.supabase.com' --oneline` → `3f80c757`, `d4369cfe`.
- Correção:
  1. **Agora**: no Supabase, resetar a senha do usuário `postgres` (ou pausar/excluir o projeto se não for mais usado). Verificar se o banco tinha dados reais de clientes; se sim, revisar logs de acesso do Supabase e avaliar comunicação de incidente (LGPD art. 48 — comunicar ANPD/titulares se houver risco relevante).
  2. Desativar o serviço `garageroute66.onrender.com` (Django antigo) se ainda existir; ele também criava superusuário `admin` e já teve senhas default no código (`create_admin.py`: `Admin@2024!Change`, `admin123` em commits antigos).
  3. Reescrever o histórico (`git filter-repo`) só **depois** da revogação e por decisão do dono — não resolve o vazamento, só reduz ruído. Como o repo é público, considerar torná-lo privado enquanto a fase de decisão durar.

**C2. Qualquer conta Manus obtém acesso total a todos os dados (autorização inexistente)**
- `protectedProcedure` (`server/_core/trpc.ts`) só verifica `ctx.user != null`. O callback OAuth (`server/_core/oauth.ts:31`) e `authenticateRequest` (`server/_core/sdk.ts:276-277`) fazem `upsertUser` de **qualquer** `openId` que o Manus autenticar — não há allowlist; `OWNER_OPEN_ID` só define `role=admin` (`server/db.ts:58`), e `role` não é usado em nenhuma rota de negócio.
- Impacto: qualquer pessoa que crie conta no Manus e faça login no app lê/edita/exclui clientes (nome, CPF, telefone, endereço), veículos, OS e financeiro (`server/routers.ts`, todas as rotas). É vazamento de dados pessoais em massa (LGPD).
- Correção: abandonar Manus OAuth. Login local para 1 usuária (ver §Autenticação). Se mantido temporariamente: allowlist por `openId` em `requireUser` + negar criação automática de usuário.

### ALTA

**A1. Dependência de terceiro para autenticação e runtime (Manus)**
- Login depende de `api.manus.im` (`OAUTH_SERVER_URL`), sessão vinculada a `VITE_APP_ID` do projeto Manus. Se a conta/projeto Manus for encerrado, ou o serviço mudar, a recepcionista não entra no sistema. Dados da usuária (nome, e-mail) são processados pelo Manus.
- O build de produção (`dist/public/index.html`, 367 KB) embute o script `manus-runtime` (~360 KB, inclui `modern-screenshot`) que escuta `postMessage` **sem validar origem** e envia para `window.parent` com target `"*"`; e carrega analytics de terceiro `https://manus-analytics.com/umami` (website-id `09f5…32ca`) com URLs de navegação (`/clients/:id`, `/quote/:id`).
- Sem `X-Frame-Options`/CSP: a página pode ser emoldurada por terceiros.
- Correção: remover `vite-plugin-manus-runtime`, `@builder.io/vite-plugin-jsx-loc`, script umami, `server/_core/{llm,map,imageGeneration,voiceTranscription,notification,dataApi}.ts`, `server/storage.ts` (proxy "forge" do Manus para S3/LLM/Maps, sem uso nas rotas) e `ComponentShowcase`/`AIChatBox`/`Map`. Adicionar `helmet` (CSP, `frame-ancestors 'none'`).

**A2. Sessão: JWT de 1 ano, não revogável, `SameSite=None`, segredo sem validação**
- Cookie `app_session_id`: `httpOnly: true` ok, mas `sameSite: "none"` (`server/_core/cookies.ts:45`) e `secure` só se a requisição chegar como HTTPS (`:46`) — em HTTP local o cookie vai sem `Secure` (e navegadores rejeitam `SameSite=None` sem `Secure`, comportamento imprevisível).
- Validade de 1 ano (`oauth.ts:41,45`, `sdk.ts:186`); JWT HS256 stateless — `logout` só apaga o cookie (`routers.ts:13`), um cookie copiado continua válido por 1 ano. Notebook compartilhado/roubado = sessão aberta.
- `JWT_SECRET` com default `""` (`server/_core/env.ts:3`), sem checagem de tamanho no boot; exemplos fracos na documentação (`QUICKSTART.md:30`, `README.md:43`, `DOCUMENTATION.md:321`). Com segredo fraco/conhecido, qualquer um forja sessão.
- `verifySession` não confere `appId` nem `iss/aud` (`sdk.ts:210-213`).
- `state` do OAuth é só `base64(redirectUri)` (`client/src/const.ts`, `sdk.ts:41-42`): sem nonce → login CSRF.
- Correção: sessão server-side (tabela/arquivo) revogável, 8–12 h com renovação, `SameSite=Lax` (ou `Strict`), `Secure` sempre em produção, segredo ≥ 32 bytes aleatórios validado no boot.

**A3. Dependências com CVEs conhecidas (`pnpm audit`: 6 críticas, 59 altas, 86 moderadas, 13 baixas)**
- Relevantes em **runtime** do servidor:
  - `axios 1.12.2` (cliente do OAuth/forge): ~11 CVEs altas (prototype pollution → MITM/vazamento de credencial, DoS) — corrigido em ≥ 1.16.0.
  - `mysql2 3.15.1`: downgrade para `mysql_clear_password` vaza senha do banco (GHSA-3f6p-5ww8-9rcr) — ≥ 3.22.0. Relevante se o MySQL for remoto.
  - `drizzle-orm 0.44.6`: SQL injection via identificadores (CVE-2026-39356) — ≥ 0.45.2. O código atual não monta identificadores dinâmicos, risco baixo hoje.
  - `express 4.21.2` → `path-to-regexp 0.1.12` (ReDoS, CVE-2026-4867), `proxy-addr 2.0.7` (crítica, CVE-2026-90711; só relevante com `trust proxy`, que não está configurado).
  - `@trpc/server 11.6.0`: CVE-2025-68130 (afeta `experimental_nextAppDirCaller`, não usado).
- Build/dev (risco no notebook/CI, não em produção): `vite 7.1.9` (leitura arbitrária de arquivo via WebSocket do dev server, CVE-2026-39363/39364) — agravado por `server.host: true` (`vite.config.ts:29`), que expõe o dev server na rede local; `vitest 2.1.9`/`tinypool` (críticas), `tar 7.5.1` (crítica + várias altas), `rollup`, `postcss`, `pnpm 10.18.0` como devDependency (várias altas: bypass de integridade do lockfile, execução de scripts).
- Saída completa: `pnpm audit --json` (rodar na raiz).
- Correção: se reaproveitar, atualizar tudo e manter `pnpm audit`/Dependabot no CI; remover `pnpm` e `add` das devDependencies.

**A4. `node_modules` (631 MB, 48.264 arquivos) e `dist` versionados — supply chain**
- Commit `e327e67c` (autor "Manus Bot", 2025-11-06) versiona `node_modules` com 13 binários nativos (`esbuild`, `rollup*.node`, `lightningcss*.node`, `tailwindcss-oxide*.node`, `fastlist-*.exe`, `onig.wasm`). Não há como provar que esses binários correspondem aos hashes do lockfile sem reinstalar e comparar; um commit futuro pode trocar um binário sem ninguém revisar (diff ilegível).
- `dist/` versionado pode divergir do fonte (já embute runtime/analytics Manus).
- `.gitignore` (Python/Django) **não ignora** `node_modules`, `dist`, nem `.env` — risco alto de o próximo `git add .` publicar o `.env` com `JWT_SECRET`/`DATABASE_URL`.
- Correção: remover `node_modules/` e `dist/` do repo, `.gitignore` com `node_modules/`, `dist/`, `.env*` (exceto `.env.example`), instalar com `pnpm install --frozen-lockfile` e build no CI; adicionar `gitleaks` como pre-commit/CI.

### MÉDIA

**M1. Custo interno das peças e margem expostos**
- `serviceOrders.get` devolve `totalCost`; `serviceOrderItems.list` devolve `unitCost` (`routers.ts` + `server/db.ts`). A página `/quote/:id` ("orçamento do cliente", `client/src/pages/ClientQuote.tsx`) consome essas mesmas rotas: mesmo que não renderize o custo, ele vai na resposta. `todo.md` marca "custos ocultos para cliente" como feito — é só ocultação visual.
- `ServiceOrderDetail.tsx:149-151` mostra custo e lucro na tela da OS — a recepcionista mostrando a tela ao cliente revela a margem.
- Se `/quote/:id` for tornado público (link por WhatsApp), IDs sequenciais permitem enumerar todos os orçamentos (IDOR) com dados pessoais.
- Correção: DTO separado para orçamento do cliente (sem custo), link público com token aleatório (≥ 128 bits) e expiração; visão "cliente" na tela sem custo/margem.

**M2. Validação de entrada fraca**
- Valores monetários como `z.string()` sem formato (`routers.ts:200,231,291`) → `parseFloat` gera `NaN`/totais inválidos; `quantity` aceita negativo/fracionário (`:199`); CPF sem validação de formato/dígito (`:43,59`); strings sem `max` (erro do MySQL vaza mensagem SQL ao cliente); `orderNumber` informado pelo cliente (`:157`) em vez de sequência do servidor.
- `serviceOrderItems.update/delete` alteram item pelo `id` sem conferir que pertence ao `serviceOrderId` informado → totais inconsistentes.
- Body limit de 50 MB em JSON/urlencoded (`server/_core/index.ts:34-35`) sem rate limit → DoS trivial.
- Correção: `z.string().regex(/^\d+(\.\d{1,2})?$/)` ou inteiros em centavos, `.int().positive()`, CPF validado e normalizado, `max()` alinhado ao schema, limite de body 100 KB, `express-rate-limit`, mensagens de erro genéricas em produção.

**M3. Exposição de rede**
- `server.listen(port)` sem host (`index.ts:60`) escuta em todas as interfaces; `findAvailablePort` (`:21,54`) troca de porta silenciosamente. No notebook, isso expõe o sistema no Wi-Fi da oficina (frequentemente compartilhado com clientes).
- Correção: bind `127.0.0.1` se uso local; se acesso remoto, só via túnel/VPN (Tailscale ou Cloudflare Tunnel com Access) com TLS; nunca porta aberta no roteador.

### BAIXA

- **B1.** Segredos/defaults de dev no histórico: `SECRET_KEY` Django com default `django-insecure-)l…0p-` (commits Django), `garage_dev_password`/`garage_password` em `docker-compose`/`init.sql`, `DJANGO_SUPERUSER_PASSWORD=admin123_mude_isso` em `.env.example` antigo. Sem impacto se nada disso estiver em produção; confirmar que o Render antigo foi desativado (ver C1).
- **B2.** `.claude/settings.local.json` versionado em commits antigos (`d0105be5`, `42e8f803`; removido em `fdf9adc3`): só permissões locais, sem segredo.
- **B3.** Logs: `console.warn("[Auth] Session verification failed", …)` a cada requisição sem cookie; `console.error` do callback OAuth e de erros de banco podem conter dados pessoais (e-mail, CPF em erro de `UNIQUE`). Sem rotação/retenção definida.
- **B4.** IDs de conta Manus no bundle (URL `files.manuscdn.com/.../310519663206785446/...`): não é segredo, mas identifica a conta.

---

## Autenticação: como funciona hoje e proposta

**Hoje:** botão de login → portal Manus (`VITE_OAUTH_PORTAL_URL/app-auth?appId&redirectUri&state`) → callback `/api/oauth/callback` troca `code` por token em `api.manus.im` (`ExchangeToken`, `GetUserInfo`) → cria/atualiza usuário → emite JWT HS256 próprio (`jose 6.1.0`, segredo `JWT_SECRET`) com `openId/appId/name`, validade 1 ano, no cookie `app_session_id`. Cada requisição valida o JWT localmente e busca o usuário no banco (se não existir, consulta o Manus de novo).

**Proposta para 1 usuária (qualquer opção de arquitetura):**
- Usuária local com senha forte (≥ 12 caracteres ou frase), hash **argon2id** (ou bcrypt cost ≥ 12); criação/reset via comando de CLI do administrador (você), não por tela pública.
- Sessão server-side revogável (tabela `sessions` ou store em arquivo), cookie `HttpOnly; Secure; SameSite=Lax`, expiração ociosa 8–12 h; logout invalida no servidor.
- Rate limit/lockout progressivo no login (ex.: 5 tentativas/15 min); log de login (sucesso/falha) sem a senha.
- Opcional: TOTP para acesso remoto. Se o sistema for só local (127.0.0.1) no notebook, a senha do app + bloqueio de tela do SO já são a principal barreira.
- Segredos só em `.env` fora do git (permissão 600) ou no gerenciador do provedor; validação no boot (falha se ausente/curto).

## LGPD

- **Dados armazenados** (`drizzle/schema.ts`): `clients` — nome, e-mail, telefone, **CPF** (único, texto puro), endereço, cidade, UF, CEP; `vehicles` — placa, chassi (VIN), cor; `users` — nome/e-mail vindos do Manus; OS e transações vinculadas ao cliente.
- **Minimização**: endereço completo, e-mail e VIN não aparecem no fluxo real (OS em papel só tem nome, CPF/CNPJ, telefone). Recomendo V1 com nome, telefone, placa/modelo/km e CPF **opcional** (só se for emitir nota/recibo). Base legal: execução de contrato (art. 7º, V) e obrigação legal/fiscal para o que for exigido em documento fiscal.
- **Retenção**: não existe política. Exclusão é hard delete sem FK/cascata (`deleteClient` apaga o cliente e deixa veículos/OS órfãos com `clientId`). Definir: OS/fiscal 5 anos; cadastro inativo anonimizado após prazo definido pelo dono; exclusão a pedido do titular com anonimização (manter OS sem identificador pessoal).
- **Terceiros/operadores**: Manus (login e analytics), Supabase/Render (histórico), futuro provedor de hospedagem/backup — listar em um registro simples de operações e preferir provedores com região/contrato claros.
- **Transparência**: aviso curto na OS impressa/WhatsApp sobre uso dos dados e contato para pedidos do titular.
- **Segurança (art. 46)**: controle de acesso (C2), cifra em repouso (disco do notebook e backup), backup cifrado, log de acesso mínimo.
- **Incidente C1**: se o Supabase teve dados reais de clientes, há potencial incidente a avaliar (art. 48).

## Riscos operacionais (notebook único na recepção)

| Risco | Severidade | Mitigação |
|---|---|---|
| Roubo/perda do notebook com banco local | Alta | Cifra de disco completa (LUKS/BitLocker), senha de SO, bloqueio automático de tela (≤ 5 min); banco nunca em pasta sincronizada sem cifra |
| Notebook como ponto único de falha (disco, ransomware) | Alta | Backup automático diário **cifrado** (ex.: `restic` para S3/Backblaze com chave guardada pelo dono fora do notebook), retenção (7 diários/4 semanais/12 mensais), teste de restore mensal |
| Malware/uso pessoal do notebook (navegação, WhatsApp Web, pendrives) | Média | Conta de SO sem privilégio de admin para a recepcionista, atualizações automáticas, antivírus nativo, navegador dedicado para o sistema |
| Exposição na internet (porta aberta, painel admin, dev server) | Alta se exposto | Nada de port forwarding; acesso remoto só via Tailscale/Cloudflare Tunnel + login; produção sem `vite dev`; bind 127.0.0.1 quando local |
| Sessão aberta na tela visível ao cliente (custo/margem, dados de outros clientes) | Média | Expiração de sessão, tela de OS sem custo por padrão, bloqueio de tela |
| Dependência de serviços de terceiros para logar (Manus) | Alta | Login local (ver acima) |

## Ações urgentes (resumo)

1. **Hoje**: resetar a senha do Postgres no Supabase `rbxt…ewyth` (ou excluir o projeto) e desativar o app antigo no Render; verificar se houve dados reais e logs de acesso.
2. Considerar tornar o repo privado durante a fase de decisão.
3. Antes de qualquer deploy deste código: corrigir `.gitignore` (`.env*`, `node_modules/`, `dist/`) e não subir com Manus OAuth (C2).
