# Parecer DBA — banco, modelo de dados e backup

Data: 2026-10-15 · Autor: agente `dba` · Fase: DECISÃO (nenhum código alterado)

## Recomendação

1. **Banco: SQLite** (modo WAL, tabelas `STRICT`, `foreign_keys=ON`), em qualquer dos dois cenários de hospedagem.
   PostgreSQL só se o `arquiteto` escolher um PaaS sem disco persistente ou um open source que o exija.
   **MySQL: descartar** — o único motivo para mantê-lo é o código atual, e o modelo atual não se aproveita (ver seção 2).
2. **Modelo atual: não reaproveitar.** Faltam o veículo na OS de forma íntegra (km, histórico), a numeração automática,
   as transições de status, a origem da peça, a aprovação, as FKs e a exclusão lógica; o fluxo de status
   é outro (`pending/in_progress/completed/paid/cancelled`). Reescrever o esquema custa menos que migrar este.
3. **Integridade no banco, não só na aplicação**: número da OS por contador transacional, transições de status
   validadas por tabela + trigger, totais derivados de view (nunca digitados), nada de `DELETE` em OS/itens/clientes.
4. **Backup**: snapshot consistente (`sqlite3 .backup`/`VACUUM INTO`) a cada hora + na saída do sistema,
   cópia cifrada fora do notebook (restic → bucket S3/B2), retenção 48 h/30 d/12 m, **restore testado automaticamente
   toda semana** e manualmente uma vez por mês. Se o orçamento permitir, Litestream para RPO de segundos.

Riscos principais: notebook como ponto único de falha (mitigado pela cópia externa); dados LGPD em backup
(mitigado por cifragem); se a escolha final for open source pronto, o banco segue o dele e este modelo vira
checklist de aceite.

---

## 1. Onde está o modelo atual

- `drizzle.config.ts:11` — dialeto `mysql`; schema em `drizzle/schema.ts`; migrações `drizzle/0000_thin_zarek.sql`,
  `drizzle/0001_skinny_wendell_vaughn.sql`. `drizzle/relations.ts` está vazio (sem relações declaradas).
- Acesso a dados: `server/db.ts`; regras (poucas) em `server/routers.ts`.
- Tabelas: `users` (Manus OAuth), `clients`, `vehicles`, `serviceOrders`, `serviceOrderItems`, `transactions`.

## 2. Lacunas e problemas (arquivo:linha)

### Integridade referencial
| # | Onde | Problema |
|---|---|---|
| 1 | `drizzle/schema.ts:53,72,73,93,115`; `drizzle/0001_skinny_wendell_vaughn.sql` (nenhuma `FOREIGN KEY`) | **Nenhuma FK.** OS pode apontar para cliente/veículo inexistente; itens órfãos. `relations.ts` vazio. |
| 2 | `server/db.ts:120-124,154-158`; `server/routers.ts:70-74,124-128` | **`DELETE` físico** de cliente e veículo. Sem FK, apagar cliente deixa OS órfãs; histórico se perde. |
| 3 | `server/db.ts:215-219`; `server/routers.ts:256-277` | Item de OS apagado fisicamente, sem checar status da OS (dá para alterar orçamento já aprovado/entregue). |
| 4 | `server/routers.ts:224-237` | `update` de item usa `id` + `serviceOrderId` vindos do cliente sem verificar que o item pertence àquela OS: recalcula o total da OS errada. |

### Numeração da OS
| # | Onde | Problema |
|---|---|---|
| 5 | `drizzle/schema.ts:74`; `server/routers.ts:157`; `client/src/pages/ServiceOrders.tsx:154-158` | **Número da OS digitado à mão** (`varchar(50)` livre). Só há `UNIQUE`; nada garante sequência, ausência de buracos ou formato. |

### Status e transições
| # | Onde | Problema |
|---|---|---|
| 6 | `drizzle/schema.ts:75` | Enum `pending/in_progress/completed/paid/cancelled` não corresponde ao fluxo real (`orcamento → aprovada → em_execucao → pronta → entregue` + `recusada`). Falta `recusada`/`aprovada`; `paid` mistura pagamento com status operacional. |
| 7 | `server/routers.ts:168-184` | `updateStatus` aceita **qualquer transição** (ex.: `paid → pending`). Não há histórico de mudanças (quem/quando), só `completedAt`/`paidAt` sobrescrevíveis (`schema.ts:81-82`). |

### Aprovação do orçamento
| # | Onde | Problema |
|---|---|---|
| 8 | `drizzle/schema.ts:70-84` | Não existe aprovação: sem data, canal (presencial/telefone/WhatsApp), quem aprovou, valor aprovado. Itens continuam editáveis depois. |

### Itens e totais
| # | Onde | Problema |
|---|---|---|
| 9 | `drizzle/schema.ts:77-78`; `server/routers.ts:207-219,239-251,262-274` | **Totais armazenados e recalculados na aplicação**, fora de transação (insert + select + update separados): duas gravações concorrentes ou falha no meio deixam total divergente. Código triplicado. |
| 10 | `server/routers.ts:212-213` | Soma com `parseFloat` (ponto flutuante) e grava com `toString()` → erros de arredondamento em dinheiro (ex.: `0.1+0.2`). |
| 11 | `drizzle/schema.ts:96` | `quantity int`: impede 4,5 L de óleo, 0,5 m de mangueira. |
| 12 | `drizzle/schema.ts:97`; `server/routers.ts:200` | `unitCost NOT NULL`: obriga informar custo, que a recepção não tem (o papel mostra que nem preço unitário é preenchido). Não há `CHECK` de valores ≥ 0 nem quantidade > 0. |
| 13 | `drizzle/schema.ts:94-95` | Peça × serviço existe (`type`), mas **sem origem da peça** (fornecedor/cliente) nem situação **devolvida ao fornecedor**; sem fornecedor. Exatamente o que hoje vai no verso do papel. |

### Veículo e histórico
| # | Onde | Problema |
|---|---|---|
| 14 | `drizzle/schema.ts:51-62` | **Sem km** (nem no veículo nem na OS). `brand`/`model` `NOT NULL` (`:54-55`) atrapalham cadastro rápido. |
| 15 | `drizzle/schema.ts:57`; `server/routers.ts:101` | Placa sem normalização (maiúscula, sem hífen) nem validação de formato (antigo/Mercosul): `ABC-1234` e `abc1234` viram veículos distintos, quebrando o histórico por placa. |
| 16 | `drizzle/schema.ts:53` | Veículo preso a um cliente; troca de dono sobrescreve `clientId` e o histórico fica atribuído ao dono atual. A OS precisa guardar o cliente da época (já guarda em `:72`, ok, mas sem FK). |

### LGPD
| # | Onde | Problema |
|---|---|---|
| 17 | `drizzle/schema.ts:35-36`; `server/routers.ts:42-43` | CPF/telefone texto livre sem normalização/validação; `UNIQUE` em CPF formatado deixa `123.456.789-00` e `12345678900` coexistirem. Sem CNPJ (o papel tem CPF/CNPJ). |
| 18 | `drizzle/schema.ts:31-43` | Sem exclusão lógica/anonimização, sem marca de retenção. Endereço/e-mail/CEP coletados sem necessidade clara na V1 (minimização). |

### Outros
| # | Onde | Problema |
|---|---|---|
| 19 | `drizzle/schema.ts:79` (e todas as tabelas) | `timestamp` MySQL: depende do fuso da sessão e limita a 2038. |
| 20 | `server/db.ts:9-19` + leituras (ex.: `:92-96`) | Se o banco não conecta, `getDb()` devolve `null` e as consultas retornam `[]`: **banco fora do ar aparece como “nenhum cliente”**. Para a recepcionista isso parece perda de dados. |
| 21 | `package.json:13` | `db:push` = `drizzle-kit generate && migrate`: gera migração na hora de aplicar; em produção migração deve ser artefato revisado e versionado. |
| 22 | `drizzle/schema.ts:109-119` | `transactions` (financeiro) ligado a OS sem FK e sem forma de pagamento; fora do escopo da V1 — remover ou adiar. |

## 3. Escolha do banco

### Comparativo para esta operação (1 usuária, ~dezenas de OS/semana, ninguém de TI)

| Critério | SQLite | PostgreSQL | MySQL |
|---|---|---|---|
| Operação no notebook | Zero: é um arquivo, sem serviço, sem senha, sem porta | Serviço Windows/Linux para manter, atualizar, monitorar | Idem PostgreSQL, com pior DX de restore |
| Operação em VPS | Arquivo no disco da VPS; app em processo único | Instalado na VPS ou gerenciado (custo extra) | Idem |
| PaaS sem disco (ex.: Vercel/Render free) | Não serve (disco efêmero) — exige volume persistente | Gerenciado: Neon/Supabase (free tier com limites e pausas) ou ~US$ 7–15/mês | Gerenciado: poucos free tiers confiáveis |
| Integridade | FK, CHECK, triggers, transações ACID; `STRICT` para tipos. Sem `DECIMAL` → dinheiro em centavos `INTEGER` | O mais completo (CHECK, triggers, `numeric`, deferrable, RLS) | Bom, mas historicamente mais permissivo (modo SQL) |
| Concorrência | 1 escritor por vez — irrelevante com 1 usuária | Sobra | Sobra |
| Backup consistente | `.backup`/`VACUUM INTO` online; Litestream para replicação contínua em S3 | `pg_dump` + WAL/PITR (pgBackRest) — mais peças | `mysqldump`/xtrabackup — mais peças |
| Restore testável | Copiar arquivo + `PRAGMA integrity_check` — segundos, automatizável | `pg_restore` em instância temporária | Idem |
| Ferramentas para leigo | DB Browser for SQLite (abre o arquivo) | pgAdmin/DBeaver | DBeaver/Workbench |
| Custo | 0 | 0 local; 0–15 US$/mês gerenciado | 0 local; gerenciado raro/caro |
| Suporte Drizzle/ORMs | Sim (dialeto `sqlite`, drivers `better-sqlite3`/libSQL) | Sim | Sim (atual) |

### Cenário A — tudo local no notebook
**SQLite, sem discussão.** Um servidor de banco no notebook é mais um serviço para quebrar em atualização do Windows,
sem ninguém para consertar. Risco real é o disco/roubo do notebook → resolvido pela cópia externa (seção 5).

### Cenário B — VPS/PaaS
- **VPS com disco (Hetzner, Lightsail, Oracle free, etc.)**: SQLite continua o melhor custo/benefício
  (app + arquivo na mesma máquina; Litestream replicando para bucket). Snapshot da VPS como camada extra.
- **PaaS sem disco persistente**: aí **PostgreSQL gerenciado** (backups/PITR do provedor + `pg_dump` diário próprio para fora do provedor).
- Em nenhum cenário MySQL ganha.

### Ponto de atenção
Escrevendo o esquema em SQL portável (sem recursos exóticos), migrar SQLite → PostgreSQL depois é trabalho de um dia
(`pgloader` ou export/import). A decisão não é irreversível.

## 4. Esboço do modelo V1 (independente de stack)

Convenções: dinheiro em **centavos INTEGER** (ou `numeric(12,2)` no PostgreSQL); quantidade em **milésimos INTEGER**
(ou `numeric(10,3)`); datas em UTC ISO-8601; nomes em português; `criado_em`/`atualizado_em` em todas.

```
cliente
  id PK
  nome                TEXT NOT NULL
  tipo_documento      TEXT NULL CHECK IN ('CPF','CNPJ')
  documento           TEXT NULL  -- só dígitos, DV validado na aplicação; CHECK length 11/14
  telefone            TEXT NULL  -- só dígitos com DDD (CHECK length 10..11)
  observacao          TEXT NULL
  excluido_em         TIMESTAMP NULL          -- exclusão lógica
  anonimizado_em      TIMESTAMP NULL          -- LGPD: nome/doc/telefone substituídos
  UNIQUE (documento) WHERE documento IS NOT NULL   -- índice parcial

veiculo
  id PK
  placa               TEXT NOT NULL UNIQUE    -- normalizada: maiúscula, sem hífen;
                                              -- CHECK placa GLOB '[A-Z][A-Z][A-Z][0-9][A-Z0-9][0-9][0-9]'
  marca, modelo       TEXT NULL
  ano                 INTEGER NULL CHECK (ano BETWEEN 1950 AND 2100)
  cliente_atual_id    FK cliente NULL ON DELETE RESTRICT
  excluido_em         TIMESTAMP NULL

contador              -- garante número sem buracos
  nome                TEXT PK  ('os')
  ultimo_valor        INTEGER NOT NULL

ordem_servico
  id PK
  numero              INTEGER NOT NULL UNIQUE -- obtido do contador NA MESMA transação do INSERT
  cliente_id          FK cliente NOT NULL ON DELETE RESTRICT  -- dono na época
  veiculo_id          FK veiculo NOT NULL ON DELETE RESTRICT
  km_entrada          INTEGER NULL CHECK (km_entrada >= 0)
  relato_cliente      TEXT NOT NULL           -- "o problema"
  diagnostico         TEXT NULL
  status              TEXT NOT NULL DEFAULT 'orcamento'
                      CHECK IN ('orcamento','aprovada','em_execucao','pronta','entregue','recusada','cancelada')
  aberta_em, entregue_em  TIMESTAMP
  -- sem coluna de total: total vem da view

transicao_status_valida   -- dados fixos; trigger BEFORE UPDATE OF status consulta e aborta se ausente
  de, para            PK (de, para)
  -- orcamento→aprovada | orcamento→recusada | orcamento→cancelada
  -- aprovada→em_execucao | aprovada→cancelada | em_execucao→pronta | pronta→entregue
  -- recusada→orcamento (cliente reconsidera)

os_status_historico      -- auditoria; preenchido por trigger AFTER UPDATE OF status
  id PK, os_id FK, de, para, em TIMESTAMP, usuario TEXT, motivo TEXT NULL

fornecedor
  id PK, nome TEXT NOT NULL UNIQUE, telefone NULL, ativo BOOLEAN

os_item
  id PK
  os_id               FK ordem_servico NOT NULL ON DELETE RESTRICT
  tipo                TEXT NOT NULL CHECK IN ('peca','servico')
  descricao           TEXT NOT NULL
  quantidade_mil      INTEGER NOT NULL DEFAULT 1000 CHECK (> 0)
  valor_unit_centavos INTEGER NOT NULL DEFAULT 0 CHECK (>= 0)
  custo_unit_centavos INTEGER NULL CHECK (>= 0)            -- opcional
  origem              TEXT NULL CHECK IN ('fornecedor','cliente','estoque')
  fornecedor_id       FK fornecedor NULL
  situacao            TEXT NOT NULL DEFAULT 'ativo' CHECK IN ('ativo','devolvido_fornecedor','removido')
  devolvido_em, motivo_devolucao   NULL
  aprovacao_id        FK aprovacao NULL       -- em qual aprovação entrou
  CHECK (tipo = 'peca' OR (origem IS NULL AND fornecedor_id IS NULL))
  CHECK (tipo = 'servico' OR origem IS NOT NULL)
  CHECK (origem = 'fornecedor' OR fornecedor_id IS NULL)
  CHECK (origem <> 'cliente' OR valor_unit_centavos = 0)   -- peça do cliente não é cobrada
  -- item nunca é apagado: "remover" = situacao 'removido'

aprovacao
  id PK
  os_id               FK ordem_servico NOT NULL
  decisao             TEXT NOT NULL CHECK IN ('aprovado','recusado')
  canal               TEXT NOT NULL CHECK IN ('presencial','telefone','whatsapp')
  aprovado_por_nome   TEXT NOT NULL
  valor_centavos      INTEGER NOT NULL        -- foto do total no momento da decisão
  em                  TIMESTAMP NOT NULL
  evidencia           TEXT NULL               -- ex.: referência ao print do WhatsApp
  -- orçamento complementar = nova linha de aprovacao para itens novos

VIEW os_totais(os_id, total_pecas, total_servicos, total_geral, custo_total)
  = soma de round(quantidade_mil * valor_unit_centavos / 1000) dos itens com situacao = 'ativo'
VIEW historico_placa = ordem_servico ⋈ veiculo ⋈ cliente ⋈ os_totais, ordenado por aberta_em
```

Triggers/regras-chave:
- `BEFORE DELETE` em `ordem_servico`, `os_item`, `aprovacao`, `os_status_historico` → `RAISE(ABORT)`.
  Cliente/veículo: `DELETE` também bloqueado; usar `excluido_em`/`anonimizado_em`.
- `BEFORE INSERT/UPDATE` em `os_item`: só permitido com OS em `orcamento`; após `aprovada`, item novo exige nova
  `aprovacao` (registrado no mesmo fluxo). Devolução (`situacao`) permitida até `pronta`.
- `aprovada` só se existir `aprovacao` com `decisao='aprovado'`; `recusada` idem com `'recusado'` (trigger).
- Numeração: `UPDATE contador SET ultimo_valor = ultimo_valor + 1 WHERE nome='os' RETURNING ultimo_valor;`
  e `INSERT` da OS na **mesma transação**. Como OS nunca é apagada, a sequência não tem buracos.
  (Não usar `AUTOINCREMENT`/`SEQUENCE`/`AUTO_INCREMENT`: no PostgreSQL e MySQL rollback consome número.)
- Índices: `ordem_servico(veiculo_id, aberta_em)`, `ordem_servico(status)`, `os_item(os_id)`, `cliente(nome)`;
  nada além disso.
- Fora da V1 (adiar, mas não bloquear): pagamento/forma de pagamento, garantia (data limite por item de serviço),
  estoque, usuários múltiplos.

### LGPD no modelo
- Base legal: execução de contrato (OS) e obrigação legal/defesa (CDC: garantia de serviço e vício oculto).
  Coletar **só** nome, documento (opcional), telefone, placa. Sem endereço/e-mail na V1.
- Retenção sugerida (validar com `seguranca`): OS e itens 5 anos após a entrega; depois anonimizar o cliente
  (manter OS e valores para histórico do veículo, sem dados pessoais).
- Pedido de exclusão do titular → anonimização (`anonimizado_em`), não `DELETE`.
- Backups contêm dados pessoais → sempre cifrados; retenção do backup ≤ retenção definida acima.

## 5. Rotina de backup (definir detalhes de agendamento com `sre`)

Premissa SQLite; equivalente PostgreSQL entre parênteses.

| Item | Proposta |
|---|---|
| Método | Snapshot online consistente: `sqlite3 os.db ".backup snap.db"` ou `VACUUM INTO` (`pg_dump -Fc`). Nunca copiar o `.db` aberto com `cp`. |
| Frequência | A cada 1 h no horário de funcionamento + ao fechar o sistema/desligar + diário às 23 h. Opcional: **Litestream** contínuo para bucket (RPO ~1 s). |
| Cópia fora do local | `restic` (cifrado, deduplicado) para bucket S3/Backblaze B2 — volume < 100 MB/ano, custo ~R$ 0–5/mês. Segunda cópia local em pendrive/HD externo é opcional, não substitui a nuvem. |
| Retenção | 48 snapshots horários, 30 diários, 12 mensais, 5 anuais (`restic forget --keep-hourly 48 --keep-daily 30 --keep-monthly 12 --keep-yearly 5 --prune`). Bucket com object lock/versionamento contra ransomware. |
| Teste de restore automático | Semanal: `restic restore latest` em diretório temporário → `PRAGMA integrity_check` = `ok` → `PRAGMA foreign_key_check` vazio → contagem de OS e `max(numero)` comparados com produção (tolerância = OS da última hora). Falha → alerta (e-mail/WhatsApp/Healthchecks.io). |
| Teste de restore manual | Mensal (ou a cada mudança de versão): subir o sistema apontando para o backup restaurado e abrir a última OS. Registrar data/resultado. |
| Monitoramento | Heartbeat a cada backup bem-sucedido (Healthchecks.io free); sem ping em 2 h de expediente → alerta para o Wesley. |
| Chaves | Senha do repositório restic guardada fora do notebook (gerenciador de senhas do responsável). Sem ela o backup é inútil. |
| Antes de migração | Snapshot obrigatório imediatamente antes de aplicar qualquer migração de esquema. |
| RPO/RTO alvo | RPO ≤ 1 h (≈ segundos com Litestream); RTO ≤ 1 h em notebook novo/VPS nova, seguindo runbook escrito pelo `sre`. |

Em VPS: somar snapshot diário do provedor, mas o backup lógico em bucket de **outro provedor** é o que conta.
Em PostgreSQL gerenciado: manter o `pg_dump` diário próprio fora do provedor, além do PITR deles.
