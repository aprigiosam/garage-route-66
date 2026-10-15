# Parecer dev (backend + frontend): código existente é reaproveitável?

Data: 2026-10-15 · Autor: agente `dev` (cobrindo também `front`) · Fase: decisão (nada alterado no código)

## Veredito

**Reaproveitar parcialmente, como molde, em repositório limpo.** Não reaproveitar o repo como está.

- O que vale é o **esqueleto** (Vite + React + tRPC + Drizzle + componentes shadcn/ui) e algumas telas de CRUD
  como ponto de partida. Compila sem erros (`tsc --noEmit` passa).
- O **domínio está raso e divergente** da OS da oficina: falta km, origem da peça, aprovação, status certos,
  numeração automática, busca por placa; as regras de negócio são CRUD sem validação.
- A **autenticação é 100% Manus** e precisa ser trocada de qualquer forma.
- O **repo está poluído** (node_modules e dist versionados, `.git` de 110 MB, histórico Django misturado):
  começar um repo novo custa menos do que limpar.

Na prática, a parte "de negócio" escrita para a oficina tem ~2.500 linhas, a maioria a ser alterada.
O ganho de partir dela em vez de um projeto novo na mesma stack é de **2 a 3 dias**, não mais.

## Esforço estimado até a V1 (1 dev, dias úteis)

| Opção | Esforço | Comentário |
|---|---|---|
| Reaproveitar o repo como está | 8–11 d | Limpeza de repo/Manus (1–2 d) + remodelagem + telas + testes; carrega dívida e histórico |
| **Reaproveitar parcialmente (repo novo, copiar o útil)** | **6–9 d** | Recomendado se a stack TS for mantida |
| Reescrever do zero na mesma stack | 8–12 d | Sem ganho real sobre a opção acima |
| Descartar e adotar open source | — | Avaliação do `arquiteto`; este parecer só diz que o código atual não é um argumento forte contra |

Detalhe da opção recomendada: auth local simples (1 usuária) 1 d; schema novo + migrações 1 d;
regras de OS (numeração, transições, totais, aprovação) com testes 2 d; telas (abrir OS rápido, busca, itens,
impressão) 2–3 d; empacotamento/deploy 1–2 d (depende de `infra`/`sre`).

## Tamanho real e estrutura

Código versionado fora de `node_modules/` e `dist/`: 131 arquivos.

| Bloco | Linhas | Situação |
|---|---|---|
| `client/src/components/ui/*` (shadcn) | ~6.200 | Gerado, reaproveitável, metade não usada |
| `client/src/pages/*` (sem Showcase) | ~1.890 | Código da oficina: CRUDs simples |
| `client/src/pages/ComponentShowcase.tsx` | 1.437 | Morto (demo do template, sem rota em `App.tsx`) |
| `server/routers.ts` + `server/db.ts` | 540 | Lógica da oficina |
| `drizzle/schema.ts` + 2 migrações | ~200 | Modelo de dados |
| `server/_core/*` + `server/storage.ts` | ~1.900 | Template Manus; ~1.300 linhas mortas |

## Modelo de dados vs domínio (`drizzle/schema.ts`)

| Requisito (docs/negocio.md) | Situação | Evidência |
|---|---|---|
| Cliente | Existe, mas CPF `unique` quebra com string vazia (ver bugs) | schema.ts:31-43 |
| Veículo / placa | Existe; placa `unique`. **Falta km** (requisito 1); `brand` obrigatório | schema.ts:51-62 |
| Histórico por placa | Não há consulta por placa; só por cliente | db.ts:182, routers.ts:146 |
| OS numerada | `orderNumber` varchar **digitado à mão** pela usuária, sem sequência | schema.ts:74, routers.ts:156, ServiceOrders.tsx:152-160 |
| Status e fluxo | Enum diferente do negócio: `pending/in_progress/completed/paid/cancelled`; sem `orçamento/aprovada/pronta/entregue/recusada` | schema.ts:75 |
| Transições | **Nenhuma validação**: qualquer status pode ir para qualquer outro | routers.ts:168-181 |
| Itens peça × serviço | Existe `type part/service` | schema.ts:95 |
| Origem da peça (fornecedor/cliente/devolvida) | **Não existe** | schema.ts:91-101 |
| Fornecedor da peça | Não existe | — |
| Aprovação do orçamento | **Não existe** (nem data, nem canal, nem quem aprovou) | — |
| Totais no servidor | Calculados no servidor, mas em `float`, sem transação e o cliente envia `serviceOrderId` separadamente do item | routers.ts:205-225 (repetido 3x: 240-257, 266-283) |
| Integridade referencial | **Sem FOREIGN KEY** em nenhuma tabela; `quantity` é `int` (não aceita 0,5 L de óleo) | 0001_skinny_wendell_vaughn.sql, schema.ts:96 |
| Pagamento | Tabela `transactions` genérica, desconectada do status `paid` | schema.ts:109-118, routers.ts:176 |

Conclusão: o schema precisa ser **refeito** (status, aprovação, origem, km, FKs, sequência, decimal em quantidade).
Como só há 2 migrações e nenhum dado de produção, não vale migrar: gerar migração inicial nova.
Observação para `dba`/`arquiteto`: é MySQL; para 1 notebook, SQLite ou Postgres local são mais leves —
Drizzle suporta ambos, então a troca de banco não invalida esta recomendação.

## Regras de negócio e APIs (tRPC, `server/routers.ts`)

Funciona de fato (compila e está ligado às telas): CRUD de clientes, veículos, OS, itens e transações;
recálculo de totais ao mexer em itens. Tudo atrás de `protectedProcedure` (exige login Manus).

Problemas:
- **Bug bloqueante**: criar cliente sem e-mail falha. O form envia `email: ""` (Clients.tsx:17,38) e o
  servidor valida `z.string().email().optional()` (routers.ts:41) — string vazia é rejeitada.
- **Bug**: segundo cliente sem CPF viola `UNIQUE(cpf)` porque o form manda `""`, não `NULL` (Clients.tsx:19, schema.ts:36).
  Na prática (negocio.md) CPF quase sempre fica em branco.
- `getDb()` sem `DATABASE_URL` devolve listas vazias em silêncio em vez de falhar (db.ts:9-19, 98-101).
- Exclusão de cliente/veículo sem checar OS vinculadas, gerando órfãos (routers.ts:72-76, 128-132).
- Lógica de totais copiada 3 vezes; nenhum `db.transaction`.
- Excluir OS: só `alert("será implementada")` (ServiceOrders.tsx:55-58).
- Sem busca no servidor; `list` traz tudo (aceitável no volume da oficina, mas não há filtro algum).
- Mudança de status no front não faz `refetch` (ServiceOrderDetail.tsx:97-106) → tela fica desatualizada.

## Acoplamento ao Manus e custo de remoção

| Ponto | Evidência | Remoção |
|---|---|---|
| OAuth Manus (login, callback, JWT, `openId`) | server/_core/sdk.ts:27-29,259; oauth.ts; context.ts:17; client/src/const.ts:10-24; main.tsx:21 | Trocar por login local (senha + sessão/cookie) — ~1 d |
| Tabela `users` baseada em `openId` | schema.ts:8-23 | Refazer junto com auth |
| "Forge" (LLM, imagem, voz, mapas, dataApi, notificação, S3 via proxy) | server/_core/llm.ts, imageGeneration.ts, voiceTranscription.ts, map.ts, dataApi.ts, notification.ts, server/storage.ts; client Map.tsx:89-93 | Apagar (nenhum é usado pelo domínio; só `notifyOwner` no systemRouter.ts:2) — minutos |
| `streamdown`, `AIChatBox`, `ManusDialog` | AIChatBox.tsx:7; ManusDialog.tsx | Apagar |
| Plugins Vite Manus | vite.config.ts:7,10,29-38 (`vitePluginManusRuntime`, `allowedHosts` *.manus.computer) | Apagar |
| Variáveis: `VITE_APP_ID`, `OAUTH_SERVER_URL`, `OWNER_OPEN_ID`, `BUILT_IN_FORGE_API_*`, `VITE_OAUTH_PORTAL_URL`, `VITE_FRONTEND_FORGE_*` | server/_core/env.ts:1-10 | Ficam só `DATABASE_URL`, `JWT_SECRET`/`SESSION_SECRET`, `PORT` |
| Deps sem uso p/ oficina | package.json: `@aws-sdk/*`, `streamdown`, `recharts`, `framer-motion`, `embla-carousel`, `@types/google.maps`, `add`, `pnpm` como devDep | Enxugar ao montar o repo novo |

Custo total de "desmanusizar": **1–2 dias**, dominado pela troca da autenticação.

## Frontend (visão da recepcionista)

Telas existentes (client/src/App.tsx:15-29): Dashboard, Clientes, Detalhe do cliente (+veículos e OS),
OS (lista), Detalhe da OS (itens, status, custo/margem), Financeiro, Orçamento imprimível (`/quote/:id`).

- **Abrir OS é lento**: diálogo com `Select` de cliente → `Select` de veículo → número digitado à mão
  (ServiceOrders.tsx:113-160). Não dá para criar cliente+veículo no mesmo fluxo nem buscar por placa.
- **Nenhuma busca** por placa, nome ou telefone em nenhuma tela (grep por `search` não encontra nada).
- Lista de OS não mostra cliente nem placa, só número e total (ServiceOrders.tsx:191-206).
- Labels de status divergentes do negócio (ServiceOrderDetail.tsx:186-192).
- Formulário de item exige "Custo Unitário" (ServiceOrderDetail.tsx:282) — dado que hoje nem existe no papel.
- **Impressão**: `ClientQuote.tsx` gera um orçamento via `window.print()` com CSS `@media print`
  (ClientQuote.tsx:28-46,171-180), sem custos internos. É o trecho de UI **mais aproveitável** como base
  da OS impressa/PDF; falta: dados da oficina, placa/km em destaque, separação peça/serviço, campo de
  assinatura/aprovação, e envio por WhatsApp.
- `Select` do Radix em todo lugar: ruim para teclado (não digita para filtrar como um combobox).
- Muitos `any` e `console.error` sem toast para a usuária (ex.: ServiceOrders.tsx:51, ServiceOrderDetail.tsx:72).

## Testes e build

- **Zero testes.** `vitest.config.ts` procura `server/**/*.test.ts`; `vitest run` → "No test files found" (exit 1).
- `tsc --noEmit` (via `node_modules` versionado): **passa sem erros**.
- `pnpm build` não executado (escreveria em `dist/`, que é versionado).

## Higiene do repo

- `node_modules/` versionado: 48.264 de 48.395 arquivos rastreados; 631 MB no disco; `.git` com **110 MB**
  (maiores blobs: mapas do mermaid, binários do esbuild e lightningcss).
- `dist/` versionado (build antigo).
- `.gitignore` é de Django/Python; não ignora `node_modules`, `dist`, `.env`.
- Sobras: `vite.config.ts.bak` (versão com `webDevPreviewerPlugin`), `todo.md` do Manus marcando como feito
  itens que não atendem o negócio, `DOCUMENTATION.md`/`QUICKSTART.md` do template, `drizzle/relations.ts` vazio
  (1 linha), `drizzle/migrations/.gitkeep` sem uso, `@assets` alias para pasta inexistente.
- Histórico com 52 commits: Django (set–out/2025) e rebuild Manus (nov/2025), commits de "Manus Bot".

Recomendação: **repo novo** (ou branch órfã) sem histórico; o antigo fica arquivado como referência.

## O que aproveitar

1. Stack/esqueleto: Vite + React 19 + tRPC 11 + Drizzle + zod + Tailwind (se o `arquiteto` mantiver TS).
2. `client/src/components/ui/*` somente os usados (button, input, label, card, dialog, table, select, sonner, badge, sidebar).
3. `client/src/components/DashboardLayout.tsx` (layout com sidebar), depois de tirar o login Manus.
4. `client/src/pages/ClientQuote.tsx` como base da OS impressa.
5. Telas `Clients.tsx`, `ClientDetail.tsx`, `ServiceOrderDetail.tsx` como rascunho de layout (lógica a refazer).
6. `server/_core/trpc.ts` (middleware `protectedProcedure`), `server/_core/vite.ts` (dev/static), `server/_core/index.ts` (sem a busca de porta).

## O que jogar fora

1. `node_modules/`, `dist/`, `.gitignore` atual, `vite.config.ts.bak`, `todo.md`, `DOCUMENTATION.md`, `QUICKSTART.md`.
2. Todo o acoplamento Manus: `server/_core/{sdk,oauth,llm,imageGeneration,voiceTranscription,map,dataApi,notification}.ts`,
   `server/storage.ts`, `server/_core/types/manusTypes.ts`, `client/src/const.ts` (getLoginUrl), `ManusDialog.tsx`,
   `AIChatBox.tsx`, `Map.tsx`, `ComponentShowcase.tsx`, plugins Vite Manus.
3. `drizzle/schema.ts` e migrações atuais (refazer: status do negócio, aprovação, origem/fornecedor da peça, km,
   FKs, numeração sequencial, quantidade decimal).
4. `transactions`/`Financial.tsx`: fora do escopo da V1 até o dono responder sobre pagamento.
5. `server/routers.ts`/`db.ts`: reescrever com serviço de OS testado (transições, totais em centavos/decimal, transação).

## Riscos

- Manter MySQL num único notebook aumenta operação/backup (decisão de `dba`/`infra`).
- Se a decisão for adotar open source, nada aqui é perda relevante: o código próprio é pequeno.
