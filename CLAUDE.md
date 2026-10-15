# Garage Route 66

Sistema de ordens de serviço para uma oficina mecânica pequena. Meta: **produção o quanto antes**.
Contexto completo do negócio: `docs/negocio.md` (leia antes de qualquer decisão).

## Fase atual: DESENVOLVIMENTO DA V1

Decisões em `docs/decisoes/0001-caminho-stack-e-infra-da-v1.md`:
- Django 5.2 LTS + SQLite, reescrita enxuta;
- Docker Compose no notebook do Wesley (fase 0) e depois Lightsail (fase 1);
- acesso só por Tailscale.

O modelo de dados segue o proposto em `docs/pareceres/dba.md`.
Repo antigo (`~/Projetos/GarageRoute66`):
- A versão React/Manus (HEAD) **não é usada**.
- A versão **Django do histórico (commit `e771b139`) é fonte de reaproveitamento seletivo**. Porte item a item,
  sempre revisado e com teste:
  - validadores BR (`core/validators.py`);
  - campos de Cliente/Veículo (`core/models.py`);
  - layout de impressão (`templates/core/public_orcamento.html`).
- Não traga do antigo: estoque, caixa, agendamento, fotos, cache, signals, settings, nem o deploy Render/Procfile.
- Os arquivos a portar foram extraídos para `legado/`, que está fora do git. **Apague cada um depois de portá-lo**;
  quando a pasta esvaziar, remova também a linha `legado/` do `.gitignore`.

## Stack e comandos

- **Python 3.12 + Django 5.2 LTS**: os dois têm suporte até 2028, numa janela só de manutenção.
- Dependências e Python são gerenciados pelo **uv**: `pyproject.toml` + `uv.lock` (com hashes) e ambiente em `.venv/`.
- `uv add <pacote>` / `uv remove <pacote>`: altera as dependências e o lock.
- `uv run python manage.py runserver`: servidor de desenvolvimento.
- `uv run python manage.py test`: testes.
- `uv run python manage.py makemigrations && uv run python manage.py migrate`: migrações.

## Princípios de engenharia

- **Pensar analiticamente:** toda escolha tem trade-off explícito, com números quando houver (custo, RAM, prazo de suporte).
- **Recursos eficientes:** o sistema roda num notebook. Nada de dependência, serviço ou processo que não se pague.
- **Sustentável:** código que o Wesley consiga manter sozinho daqui a 2 anos. Explícito vence esperto.
  Use o que o Django já oferece antes de adicionar uma biblioteca, e só versões com suporte (LTS).
- **Reprodutível:** dependências travadas no lock, e o mesmo Python no desenvolvimento e no container.

## Restrições que guiam tudo

- 1 usuária (recepcionista), 1 notebook na oficina e nenhum time de TI local.
- O dono não é técnico: operação e backup precisam ser automáticos ou triviais.
- Custo mensal baixo; preferir o que é simples e conhecido a soluções "modernas".
- Dados de clientes (nome, CPF, telefone, placa) estão sujeitos à LGPD.

## Time (subagentes em `.claude/agents/`)

| Agente | Papel |
|---|---|
| `arquiteto` | Decide entre reaproveitar, adotar open source ou reescrever; define stack e escreve os ADRs |
| `dev` | Backend, modelo de dados e regras de negócio |
| `front` | Interface da recepcionista: rápida, simples, sem treinamento |
| `qa` | Testes, critérios de aceite e revisão do que os outros entregam |
| `dba` | Banco, modelagem, integridade, migrações e backup/restore do banco |
| `infra` | Onde o sistema roda: hospedagem, rede, DNS/HTTPS, IaC e custo mensal |
| `sre` | Mantê-lo de pé: CI/CD, deploy/rollback, backup testado, monitoramento e incidentes |
| `seguranca` | LGPD, autenticação, segredos, dependências e exposição |

O agente principal coordena: distribui as tarefas, consolida os pareceres e leva as decisões ao usuário.

## Modo aprendizado (obrigatório)

O Wesley quer **aprender durante todo o processo**. Ele é forte em infra/AWS/banco e está aprendendo
desenvolvimento (Python/Django). Por isso:
- Trabalhe em **passos pequenos**. Antes de cada passo, diga o que vai fazer e por quê, em 2 ou 3 linhas.
- **Infra, banco e operação** (Docker, Tailscale, backup, Terraform): ele executa os comandos; você orienta e revisa.
- **Código**: escreva em incrementos pequenos e explique os conceitos novos de Django na primeira vez que aparecerem.
  Quando fizer sentido, deixe-o escrever a próxima parte parecida.
- Registre o que foi aprendido em `docs/aprendizado.md`: conceito, onde apareceu no projeto e link da documentação oficial.
- Ensinar não é ser prolixo: nada de explicar o básico de infra, que ele domina.

## Convenções

- Tudo em português (código pode ter identificadores em inglês).
- Decisões viram ADR em `docs/decisoes/NNNN-titulo.md`: contexto, opções, decisão e consequências.
- Pareceres são objetivos: recomendação primeiro, justificativa curta e riscos.
- Toda mudança é documentada (README/changelog). O usuário é especialista em infra: sem explicações básicas.
