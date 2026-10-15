# Operação: runbook

Como subir, atualizar, diagnosticar e recuperar o sistema. Comandos executados na raiz do repositório,
no servidor (fase 0: notebook do Wesley).

## Estado da produção

| Item | Situação |
|---|---|
| Aplicação em container | ✅ no ar em `127.0.0.1:8000` (só o servidor acessa) |
| Backup automático cifrado + restore testado | ⛔ **pendente: não cadastrar dados reais antes disso** |
| Acesso da oficina via Tailscale (HTTPS) | ⛔ pendente |
| OS impressa/PDF | ⛔ pendente |
| CI/CD | ⛔ backlog |

## Componentes

| Componente | Onde |
|---|---|
| Container | serviço `app` do `compose.yaml`, imagem `garage-route-66:latest` |
| Banco | `/data/db.sqlite3` no volume Docker `garage-route-66_dados` (WAL: também `-wal` e `-shm`) |
| Configuração | `.env.prod` na raiz do repo (fora do git, permissão 600) |
| Logs | stdout do container (`docker compose logs`): acessos do gunicorn + erros |
| Healthcheck | `GET /saude/`: `200 {"status":"ok"}` ou `503` se o banco falhar; o Docker checa a cada 30s |

## Tarefas comuns

```bash
docker compose ps                                   # estado e saúde
docker compose logs -f --tail=100                   # logs
docker compose up -d --build                        # atualizar para o código atual (migra o banco na subida)
docker compose restart                              # reiniciar
docker compose down                                 # parar (os dados ficam no volume)
docker compose exec app python manage.py createsuperuser        # novo usuário admin
docker compose exec app python manage.py changepassword <user>  # trocar senha
docker compose exec app python manage.py shell                  # console Python com os models
```

Comandos que pedem senha (`createsuperuser`, `changepassword`) precisam de um terminal interativo (TTY).
Rode-os num terminal normal, não pelo prompt `!` do Claude Code.

**Atualizar com segurança:**
1. `git pull`
2. Testes: `uv run --env-file .env python manage.py test oficina`
3. *(quando existir)* backup manual
4. `docker compose up -d --build`
5. Conferir o healthcheck: `docker compose ps` deve mostrar `healthy`.

O container sobe sozinho com o servidor (`restart: unless-stopped`). Em horário de expediente,
o notebook-servidor não pode suspender.

## Variáveis de ambiente (`.env.prod`)

| Variável | Obrigatória | Exemplo / padrão | Para quê |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | **sim** | gerar com o comando do `.env.example` | Assina sessões e CSRF. Sem ela o app não sobe. **Diferente da de dev** |
| `DJANGO_DEBUG` | não | `0` (padrão) | Nunca `1` em produção |
| `DJANGO_ALLOWED_HOSTS` | sim | `127.0.0.1,localhost,<host>.ts.net` | Hosts aceitos. `127.0.0.1` é usado pelo healthcheck |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | com HTTPS | `https://<host>.<tailnet>.ts.net` | Origem dos formulários sob HTTPS |
| `DJANGO_DB_PATH` | não | `/data/db.sqlite3` (definido na imagem) | Caminho do banco |
| `DJANGO_STATIC_MANIFEST` | não | `1` (definido na imagem) | Estáticos com hash; só funciona após o `collectstatic` do build |

## Problemas comuns

| Sintoma | Causa provável | Ação |
|---|---|---|
| `KeyError: 'DJANGO_SECRET_KEY'` na subida | `.env.prod` ausente ou sem a chave | Criar/corrigir o `.env.prod` |
| `400 Bad Request` | Host não está em `DJANGO_ALLOWED_HOSTS` | Adicionar o host e rodar `docker compose up -d` |
| `403 CSRF verification failed` ao salvar | Origem HTTPS fora de `DJANGO_CSRF_TRUSTED_ORIGINS` | Adicionar `https://<host>` |
| Container `unhealthy` | Banco inacessível (volume, disco cheio) | `docker compose logs`, `df -h`, `docker volume inspect garage-route-66_dados` |
| `database is locked` | Escrita concorrente longa (não deve ocorrer com WAL + IMMEDIATE + busy_timeout 5s) | Ver logs; reportar como bug |
| Admin sem CSS | Imagem antiga ou build sem `collectstatic` | `docker compose up -d --build` |

## Backup e restauração

⛔ **Pendente: próxima etapa.** Plano (ver `docs/pareceres/dba.md` §5):
- cópia consistente do SQLite a cada hora (`sqlite3 .backup`), nunca copiar o arquivo com o app gravando;
- `restic` cifrado para o S3, com retenção e restore testado toda semana;
- alerta de falha (Healthchecks.io).
