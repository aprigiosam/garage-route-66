# ADR 0001 — Caminho, stack e infraestrutura da V1

- **Status:** Aceito em 2026-10-15 (o Wesley deu o sinal para desenvolver)
- **Data:** 2026-10-15
- **Base:** `docs/pareceres/` (arquiteto, dev, dba, infra, seguranca)

## Contexto

A oficina tem 1 recepcionista, 1 notebook e nenhum técnico local, e precisa entrar em produção rápido
(ver `docs/negocio.md`). O repo atual foi gerado pelo Manus (React + Express/tRPC + MySQL) e foi auditado:
- o código próprio da oficina tem ~2.500 linhas, e o resto é template;
- o modelo de dados não segue o fluxo real (22 problemas apontados pelo dba);
- não há testes;
- o login depende 100% do Manus, e qualquer conta Manus vira usuária com acesso total;
- há 6 CVEs críticas e 59 altas nas dependências;
- `node_modules` e `dist` estão versionados;
- o repo é público e o histórico expõe uma credencial de banco (Supabase).

## Decisão

1. **Caminho: reescrita enxuta num repo novo.** O repo atual não é reaproveitado como base.
   - Do código atual, só ideias de tela (layout de OS impressa).
   - Do histórico Django (`e771b139`), só o que servir de modelo de domínio.
   - Open source: nenhum candidato atende sem ressalvas. O Torqvoice é o mais aderente, mas tem
     licença ELv2, 1 mantenedor, 8 meses de vida e dinheiro guardado em float. Fica descartado para produção.
2. **Stack: Django + SQLite.**
   - O Django admin em pt-BR cobre os cadastros. Ficam só as telas próprias da OS e uma página de impressão/PDF.
   - Autenticação, sessão server-side revogável, CSRF e argon2 já vêm prontos. Isso resolve o
     bloco inteiro de achados de auth do parecer de segurança sem escrever código de auth.
   - SQLite (WAL, FKs, `STRICT`), com o modelo da V1 proposto pelo dba: OS numerada sem buracos,
     transições de status validadas, itens peça/serviço com origem, valores em centavos, sem DELETE físico.
   - *Alternativa rejeitada:* manter React/tRPC/Drizzle como molde (parecer dev). Economiza 2–3 dias,
     mas traz mais código para manter, auth a escrever do zero e a árvore de dependências que gerou as CVEs.
3. **Infra em duas fases, mesmo artefato (Docker Compose):**
   - **Fase 0, agora, custo zero:** o servidor é o **notebook do Wesley**. Decisão dele: o dono ainda não aprovou gastos.
   - **Fase 1, quando o dono aprovar:** **Lightsail São Paulo (2 GB, ≈ R$ 62/mês)**, provisionado via Terraform.
     A migração é restaurar o backup do SQLite e subir o mesmo Compose.
4. **Acesso: sem exposição pública, nas duas fases.**
   - O acesso é por **Tailscale**: o notebook da oficina e o servidor (o note do Wesley, depois o Lightsail)
     entram na tailnet, com HTTPS por certificado da própria Tailscale. Nenhuma porta fica aberta no roteador nem no firewall.
   - Isso concilia a nuvem (parecer infra) com "não expor na internet" (parecer seguranca) e dispensa domínio.
5. **Backup:**
   - `sqlite3 .backup` a cada hora + `restic` cifrado para S3, com retenção e restore testado semanalmente;
   - alerta de falha via Healthchecks.io;
   - meta: RPO ≤ 1 h, RTO ≤ 1 h.
6. **Notebook da oficina:** disco cifrado, navegador com atalho em modo app, hotspot 4G como plano B
   e bloco de OS em papel com numeração reservada.

## Pré-requisitos antes da produção

- [ ] **Revogar a credencial Supabase vazada** e desativar o app antigo no Render (urgente, independe deste ADR).
- [ ] Repo antigo: tornar privado ou arquivar. O desenvolvimento segue no repo novo `garage-route-66`.
- [ ] Medir a internet da oficina por 1–2 semanas. Se reprovar, o mesmo sistema roda no notebook da oficina
      (SQLite + Compose), sem reescrita.
- [x] Escopo confirmado (2026-10-15): **sem estoque** (peças cotadas em autopeças por OS) e **sem fiado**
      (pagamento registrado na entrega). Nenhum open source volta à mesa.

## Riscos da fase 0 (notebook do Wesley como servidor)

- **Disponibilidade:** a oficina só funciona se o note estiver ligado, sem suspender e online no horário comercial.
  Mitigação: desativar a suspensão durante o expediente, iniciar o Compose com o sistema (`restart: unless-stopped`)
  e manter o bloco de OS em papel como contingência.
- **Recursos:** o note já roda outros projetos (k3d). O app em Django + SQLite usa pouca RAM, mas evite deixar o cluster k3d ligado junto.
- **Dados de clientes num note pessoal:** disco cifrado e backup cifrado fora do note são obrigatórios desde o primeiro dia (LGPD).

## Consequências

- V1 estimada em 1–2 semanas de desenvolvimento. Custo de ≈ R$ 0 na fase 0 (S3 de backup: centavos)
  e ≈ R$ 65–70/mês na fase 1 (Lightsail + snapshots + S3).
- Uma stack e um processo só, sem banco separado para operar.
- O SQLite limita a concorrência de escrita. É irrelevante para 1 usuária; ao crescer, migrar para PostgreSQL via ORM.
- Dependência da internet da oficina, mitigada pelo 4G e pelo papel de contingência.
