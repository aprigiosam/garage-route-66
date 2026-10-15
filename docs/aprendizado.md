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
