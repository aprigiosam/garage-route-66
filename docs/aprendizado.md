# Diário de aprendizado

Conceitos aprendidos ao longo do projeto: o que é, onde apareceu aqui e a documentação oficial.

| Data | Conceito | Onde apareceu | Documentação |
|------|----------|---------------|--------------|
| 2026-10-15 | **Project × app**: o project (`config/`) guarda a configuração e as rotas globais; a app (`oficina/`) é um módulo de domínio com models, views e admin próprios | `config/`, `oficina/` | https://docs.djangoproject.com/en/5.2/ref/applications/ |
| 2026-10-15 | **`manage.py`**: o CLI do projeto (servidor, migrações, testes, shell). Ele já carrega o `config.settings` | `manage.py` | https://docs.djangoproject.com/en/5.2/ref/django-admin/ |
| 2026-10-15 | **uv + versão do Python**: `requires-python = ">=3.12"` deixou o uv escolher o 3.15, que o Django 5.2 não suporta. A correção foi travar com `~=3.12.0` e `.python-version` | `pyproject.toml`, `.python-version` | https://docs.astral.sh/uv/concepts/python-versions/ |
| 2026-10-15 | **`uv.lock`**: lock com hashes, versionado no git. `uv sync` recria o `.venv` idêntico em qualquer máquina | `uv.lock` | https://docs.astral.sh/uv/concepts/projects/sync/ |
| 2026-10-15 | **Settings via ambiente (12-factor)**: `os.environ["X"]` para o obrigatório (falha cedo), `.get()` com padrão seguro para o opcional. `.env` fora do git, `.env.example` versionado | `config/settings.py` | https://docs.djangoproject.com/en/5.2/topics/settings/ |
| 2026-10-15 | **`check --deploy`**: checklist de segurança de produção que já vem no Django | `manage.py check --deploy` | https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ |
| 2026-10-15 | **Constraints no banco** (`CheckConstraint`/`UniqueConstraint` em `Meta`): a regra vale mesmo se o código for contornado; o teste prova com `IntegrityError` | `oficina/models.py` | https://docs.djangoproject.com/en/5.2/ref/models/constraints/ |
| 2026-10-15 | **`Decimal` arredonda como banco por padrão** (meio para o par): 139,965 → 139,96. Valor cobrado usa `ROUND_HALF_UP` | `ItemOS.valor_total` | https://docs.python.org/3/library/decimal.html#rounding-modes |
| 2026-10-15 | **`localize=True`** nos campos decimais para aceitar "154,00" | `oficina/admin.py` | https://docs.djangoproject.com/en/5.2/topics/i18n/formatting/ |
| 2026-10-15 | **`setUpTestData`**: cria dados uma vez por classe de teste (suíte de 4,7s para 1,3s) | `oficina/tests/test_admin.py` | https://docs.djangoproject.com/en/5.2/topics/testing/tools/#django.test.TestCase.setUpTestData |
| 2026-10-15 | **Multi-stage build**: o estágio de build tem uv e cache; o runtime leva só o `.venv` e o código (249 MB, roda com ~93 MB de RAM) | `Dockerfile` | https://docs.astral.sh/uv/guides/integration/docker/ |
| 2026-10-15 | **SQLite em WAL + `transaction_mode=IMMEDIATE`**: vários workers do gunicorn sem "database is locked" | `config/settings.py` | https://docs.djangoproject.com/en/5.2/ref/databases/#sqlite-transaction-behavior |
| 2026-10-15 | **Manifest de estáticos só no container**: o hash no nome permite cache imutável; em dev/teste não existe o collectstatic | `STORAGES` em `config/settings.py` | https://whitenoise.readthedocs.io/en/stable/django.html |
