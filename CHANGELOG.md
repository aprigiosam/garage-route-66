# Changelog

Mudanças relevantes do sistema, da mais recente para a mais antiga.

## 2026-10-15

### Adicionado
- **Telas do balcão** (app `balcao`): login; quadro de OS por status com busca enquanto digita (placa, nome,
  telefone ou nº); nova OS a partir da placa (placa nova cria cliente e veículo; cliente com o mesmo CPF/CNPJ é
  reaproveitado); detalhe da OS com itens, totais, resposta do cliente, mudança de status, entrega com forma de
  pagamento, devolução/remoção de item e histórico.
- Teste que reproduz o `collectstatic` do build (pegou referência a `.map` inexistente no Bootstrap, que quebrava a imagem).
- ADR 0002: monolito modular; interface com Django templates + HTMX + Bootstrap (vendorizados, sem Node).
- Documentação de sustentação: `README.md`, `docs/dominio.md` (regras de negócio), `docs/operacao.md` (runbook) e este changelog.
- Container de produção: Dockerfile multi-stage (Python 3.12, uv, gunicorn, whitenoise) e `compose.yaml` com hardening
  (não-root, somente leitura, sem capabilities, 256 MB, porta só no loopback). Healthcheck em `/saude/`.
- SQLite em WAL com transações `IMMEDIATE` e `busy_timeout` para suportar vários workers.
- Domínio da OS: cliente, veículo, fornecedor, OS com numeração sem buracos, transições de status, aprovação com valor
  congelado, histórico, itens peça/serviço com origem e devolução. Exclusão bloqueada.
- Interface da recepcionista no Django admin: busca por placa, nome ou telefone; itens dentro da OS; "Próximo passo".
- Validadores BR: CPF, CNPJ (inclusive alfanumérico, vigente desde jul/2026), placa (antiga e Mercosul) e telefone.
- Configuração via variáveis de ambiente (12-factor), pt-BR e fuso de São Paulo.

### Corrigido (pego pelos testes antes de ir ao ar)
- Telefone, CPF/CNPJ e placa digitados com máscara eram recusados por tamanho antes de serem normalizados
  (afetava também o admin). Agora normaliza antes de validar (migração 0002).
- Arredondamento de valores: era bancário (139,965 → 139,96); agora é comercial (139,97).
- Campos de valor recusavam "154,00" com vírgula.
