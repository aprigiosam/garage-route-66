# Parecer do arquiteto: reaproveitar, adotar open source ou reescrever

Data: 2026-10-15 · Fase: DECISÃO (nenhum código alterado)

## Recomendação

**Caminho C: reescrita enxuta em Django + SQLite** (Django admin em pt-BR para os cadastros, mais 3 ou 4 telas
próprias para a OS e uma página de impressão/PDF). A base é o **modelo de domínio Django que já existe no
histórico deste repo** (commit `e771b139`, 29/10/2025, antes do rebuild do Manus). Ele é aproveitado de forma
seletiva, não restaurado inteiro.

- **Descartar o código Manus atual (A).** Ele resolve pouco do fluxo real e é preso ao Manus: OAuth, "forge API",
  plugin de Vite. Também carrega muito boilerplate.
- **Não adotar MapOS nem Odoo (B).** O MapOS é maduro e brasileiro, mas foi feito para assistência técnica. Não
  tem veículo/placa nem origem da peça, e cada item da OS precisa de um produto cadastrado. Adaptá-lo significa
  manter um fork em PHP/CodeIgniter. O Odoo é pesado demais para 1 usuária.
- **Plano B com prazo fixo: Torqvoice.** É o open source mais aderente a oficina (veículo com placa e km, peças e
  mão de obra separadas, orçamento com aprovação, status configuráveis, tradução pt-BR, Docker). Antes de começar a
  reescrita, sugiro **meio dia de test-drive** dele em pt-BR com a recepcionista, **sem fork**. Se cobrir ~80% da V1
  usando só configuração e campos customizados, adota-se o Torqvoice como está. Se não cobrir, segue a reescrita.

Por que C e não o "pronto": a V1 é pequena (≈6 tabelas). Com Django, autenticação, CRUD, migrações, admin e i18n
vêm de graça. SQLite em arquivo único funciona igual no notebook (sem internet) e numa VPS/Lightsail, e o backup é
copiar um arquivo. Isso neutraliza a pergunta em aberto sobre a internet.

## Tabela comparativa

| Critério | A. Repo atual (Manus) | B1. MapOS | B2. Torqvoice | C. Reescrita Django + SQLite |
|---|---|---|---|---|
| Aderência ao fluxo (cliente+veículo, status, peça/serviço, origem, aprovação) | Baixa a média. Tem veículo/placa e tipo peça/serviço. Status `pending/in_progress/completed/paid` não batem com o fluxo. Sem origem da peça, sem aprovação, sem km | Baixa a média. Sem veículo/placa (iria em texto livre). Status próximos (Orçamento, Aprovado, Em Andamento, Aguardando Peças, Finalizado, Faturado). Item exige produto cadastrado. Sem origem da peça | **Alta.** Veículo com placa/km/VIN, peças × mão de obra, orçamento com aprovação, status próprios, portal do cliente. Origem da peça só via campo customizado/categoria. Sem CPF/CNPJ nativo | **Total**, porque é modelado para o caso, inclusive origem da peça (fornecedor/cliente/devolvida) e status do `negocio.md` |
| BR (pt-BR, R$, CPF/CNPJ) | UI em inglês misturado. Campo `cpf` existe | **Nativo** (pt-BR, CPF/CNPJ, R$) | Tradução pt-BR existe. Moeda BRL não verificada. Sem CPF | Nativo (django `pt-br`, validação de CPF/placa simples) |
| Impressão/PDF | Página de orçamento HTML. Sem PDF | Sim (mPDF) | Sim (layouts de documento) | HTML de impressão + "Salvar como PDF" do navegador (V1) |
| Tempo até produção (estimativa) | 2–3 semanas: remover Manus, auth local, remodelar, PDF, limpar repo | 1 dia se usado como está (com gambiarras). 2+ semanas para adaptar o fork | **1 dia** se usado como está | **1–2 semanas** para a V1 |
| Operação | Node + MySQL: 2 processos, build TS, `pnpm` | PHP 8.4 + MySQL (+ phpMyAdmin) | Docker: Next.js + Postgres 16. Atualizações muito frequentes | 1 processo Python + 1 arquivo SQLite. Backup = cópia do arquivo |
| Manutenção/risco | Código gerado, sem testes, 1.4k linhas de showcase, `node_modules` versionado | Comunidade grande. Fork diverge do upstream. Legado CodeIgniter/jQuery | **Bus factor 1** (≈99% dos commits de 1 autor), projeto de fev/2026, dinheiro em `Float` | Código pequeno e próprio. Depende de quem mantém (o usuário) |
| Licença / lock-in | MIT declarada. **Lock-in Manus** (OAuth, forge API, `vite-plugin-manus-runtime`) | Apache-2.0 | **Elastic License 2.0**: uso interno OK, proíbe oferecer como SaaS a terceiros. Não é OSI | Própria |

## Candidatos open source avaliados

| Projeto | Stack | Licença | Atividade (consulta em 15/10/2026) | Veredito |
|---|---|---|---|---|
| [RamonSilva20/mapos](https://github.com/RamonSilva20/mapos) | PHP 8.4, CodeIgniter, MySQL, Bootstrap/jQuery, mPDF. Docker compose e scripts de instalação | Apache-2.0 | ~1.1k stars, 691 forks, 8 issues abertas, release v4.55.2 em 14/10/2026. Ativo desde 2016 | Melhor OS brasileira **genérica**. Serve de referência ou de "quebra-galho imediato", mas tem baixa aderência a oficina |
| [Torqvoice/torqvoice](https://github.com/Torqvoice/torqvoice) | Next.js, TypeScript, Prisma, PostgreSQL. Docker (`ghcr.io/torqvoice/torqvoice`) | ELv2 (source-available) | 42 stars, release v1.2.61 em 13/10/2026 (quase diária). Criado em fev/2026. 1 mantenedor principal | **Mais aderente** a oficina. Bom para test-drive. O risco está na longevidade e na licença |
| [aon082910/repair-hub](https://github.com/aon082910/repair-hub) | Django 5 + SQLite, 1 container | MIT | 3 stars, criado em set/2026 | Arquitetura ideal para o caso (orçamento com link de aprovação e assinatura, PDF), mas **novo demais**. Só como referência de design |
| Odoo Community 19 + [OCA/repair](https://github.com/OCA/repair) + [OCA/l10n-brazil](https://github.com/OCA/l10n-brazil) | Python, PostgreSQL | LGPL-3 (core) / AGPL-3 (OCA) | Muito ativo | Robusto e brasileiro, mas **pesado demais** para 1 usuária: upgrades anuais trabalhosos e ERP inteiro para operar. Descartado na V1 |

Descartados por estarem mortos, arquivados ou serem só demonstração:
[GarageBuddy](https://github.com/dimitar-grigorov/GarageBuddy) (C#, sem push desde jan/2024),
[automotive-repair-management-system](https://github.com/ChanMeng666/automotive-repair-management-system) (arquivado),
[wangonya/auto-repair-saas](https://github.com/wangonya/auto-repair-saas) (2021),
[bbroger/oficina-mecanica](https://github.com/bbroger/oficina-mecanica) (2020),
[fvandrad/oficina-mecanica](https://github.com/fvandrad/oficina-mecanica) (front com JSON Server, é um protótipo),
[EdwinVW/pitstop](https://github.com/EdwinVW/pitstop) (demo de arquitetura de microsserviços, não é produto).
Os demais resultados em pt-BR no GitHub são TCCs ou projetos de curso com menos de 20 stars.

## Visão rápida do repo atual (para comparação; a auditoria detalhada é do `dev`)

- **Histórico:** são 52 commits. Até 29/10/2025 o app era **Django** (`core/models.py` com ~1.000 linhas: Cliente,
  Veículo, OS com status `ABERTA → DIAGNOSTICO → ORCAMENTO → ORCAMENTO_ENVIADO → APROVADA → EM_ANDAMENTO →
  AGUARDANDO_PECA → CONCLUIDA → ENTREGUE/CANCELADA`, itens PEÇA/SERVIÇO/TERCEIRO, pedido de peça com fornecedor,
  pagamentos, caixa, estoque, fotos, histórico de status, link público, testes e CI). Em 06/11/2025 tudo foi
  substituído pelo app do Manus. **Esse modelo Django é o ativo mais valioso do repo**, apesar de estar
  superdimensionado (estoque, caixa, agendamento, cache).
- **App atual:** React 19 + Express + tRPC + Drizzle/MySQL. O domínio real ocupa ~300 linhas de router, ~240 de
  `db.ts` e 6 páginas. O resto é template Manus: `ComponentShowcase` (1.437 linhas), `AIChatBox`, `Map`, `llm.ts`,
  `voiceTranscription`, `imageGeneration`, S3. O schema tem 5 tabelas, status sem "orçamento/aprovada/entregue",
  sem km, sem origem da peça e sem aprovação. Não há testes.
- **Lock-in Manus:** `OAUTH_SERVER_URL=api.manus.im`, `BUILT_IN_FORGE_API_*`, `vite-plugin-manus-runtime`,
  `ManusDialog`. Sem o Manus, não há login.
- **Higiene:** **48.264 dos ~48.400 arquivos versionados são `node_modules`**, `.git` ocupa 110 MB e `dist/` também
  está versionado. O `.gitignore` é o do Django (não ignora `node_modules`). O README diz "MIT/código aberto" e o
  repo pode estar público, o que deve ser conferido pelo agente `seguranca` (LGPD e segredos no histórico).

## Premissas assumidas (perguntas em aberto no `negocio.md`)

1. **Internet:** desconhecida, então tratada como **não confiável**. A solução precisa rodar **local no notebook**
   e também poder ir para a nuvem sem reescrita. Django + SQLite atende os dois casos. Torqvoice/MapOS exigem
   Docker ou servidor web + banco no notebook, o que é viável mas dá mais operação.
2. **Estoque:** **não há estoque na V1**. As peças são compradas por OS, cada uma com origem (fornecedor/cliente)
   e com a possibilidade de ser marcada como devolvida. Custo e margem por item ficam como campo opcional.
3. **Pagamento:** a V1 registra só forma e valor pagos na entrega, sem contas a receber, parcelamento ou fiado.
4. **Saída da OS:** página HTML de impressão e "Salvar como PDF" para enviar por WhatsApp manualmente. Sem
   integração com WhatsApp na V1.
5. **Aprovação:** registro manual pela recepcionista (data, canal presencial/telefone/WhatsApp e quem aprovou).
   Link público de aprovação fica para depois.
6. **Backup:** automático e fora do notebook, com cópia diária do SQLite para S3 ou equivalente e restore testado.
   É responsabilidade de `infra`/`sre`, e o desenho de C torna isso trivial.

Se a resposta para "estoque" ou para "fiado/contas a receber" for **sim**, a vantagem do caminho C diminui e vale
reavaliar MapOS ou Torqvoice, que já trazem essas funções.

## Riscos

| Risco | Caminho | Mitigação |
|---|---|---|
| Reescrita cresce além da V1 (repetir o superdimensionamento do Django antigo) | C | Escopo fechado nos 5 requisitos do `negocio.md`. Estoque, caixa e agendamento ficam fora até nova decisão |
| Bus factor 1 (o usuário mantém sozinho) | C | Stack chata e documentada (Django LTS, SQLite), código pequeno, testes do fluxo da OS |
| Notebook como ponto único de falha | Todos | Backup externo automático e restore ensaiado. Opção de rodar na nuvem se a internet for boa |
| Torqvoice descontinuado ou com mudança de licença; releases diárias quebrando | B2 | Usar só como está, com versão fixada, e exportar os dados periodicamente. Não fazer fork |
| Fork do MapOS divergindo do upstream | B1 | Não fazer fork. Se usado, só como está |
| Dados pessoais (CPF, telefone, placa) em repo/histórico público | A, C | Revisão do `seguranca`. Novo repo ou histórico limpo sem `node_modules`/`dist` |
| Migração de dados futura (se a decisão mudar) | Todos | Modelo simples e exportação CSV desde a V1 |

## Próximos passos sugeridos

1. Perguntar ao dono as questões em aberto, principalmente estoque, fiado e internet.
2. Fazer o test-drive de meio dia do Torqvoice (Docker local, pt-BR, BRL) com um caso real de OS.
3. Se o Torqvoice não atender, abrir o ADR `docs/decisoes/0001-...` com o caminho C e definir o repo (novo ou
   branch órfã limpa). Depois, o `dev`/`dba` extraem do commit `e771b139` só os modelos da V1.
