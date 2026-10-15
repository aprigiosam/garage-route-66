# ADR 0002: Monolito modular e interface com Django templates + HTMX

- **Status:** Aceito em 2026-10-15
- **Contexto:** o admin funciona, mas a recepcionista precisa de telas pensadas para o balcão. A dúvida era
  separar o sistema em serviços (SPA de front + API de back + banco) ou manter uma aplicação só.

## Decisão

1. **Monolito modular:** uma aplicação Django, um container e o SQLite como arquivo no volume. Divisão interna:
   - `oficina/`: **domínio** (models, regras, validadores). Não depende de nenhuma interface.
   - `balcao/`: **interface da recepcionista** (views, templates). Só chama as regras do domínio.
   - Django admin: **backoffice** (fornecedores, correções).
2. **Interface renderizada no servidor** (Django templates) com **Bootstrap 5.3** e **HTMX 2**, vendorizados em
   `balcao/static/balcao/vendor/` (versões fixas, hashes em `SHA256SUMS`, sem CDN e sem build com Node).
3. **HTMX só onde dá ganho real** (busca enquanto digita, consulta de placa). Ações usam formulário comum + redirect:
   funcionam sem JavaScript e são simples de testar.

## Alternativas rejeitadas

| Opção | Por que não |
|---|---|
| SPA (React) + API + PostgreSQL | 3 serviços, ~4–6× mais RAM, 2 linguagens/toolchains, código ~2× por tela, regras duplicadas, auth por token, +50–100% de prazo. O ganho (interface "app-like") é coberto pelo HTMX |
| Microsserviços | Nenhum problema que justifique |

## Quando reavaliar

- App de celular para mecânicos → API (Django REST) **dentro do monolito**, sem separar o deploy.
- Várias oficinas (SaaS) ou escrita concorrente alta → PostgreSQL em container próprio; o ORM isola a troca.
