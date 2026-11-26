#!/usr/bin/env bash
# Uso: bash scripts/deploy.sh [preview|prod]
# Provedor via DEPLOY_PROVIDER (netlify|vercel|cloudflare). Lê .env se existir.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
MODE="${1:-preview}"
PROVIDER="${DEPLOY_PROVIDER:-netlify}"
NAME="${PROJECT_NAME:-garageroute66-demo}"

echo ">> Build (GA4=${GA4_ID:-off} Clarity=${CLARITY_ID:-off})"
node scripts/build.mjs

case "$PROVIDER" in
  netlify)
    FLAGS="--dir=dist --site=$NAME"; [ "$MODE" = prod ] && FLAGS="$FLAGS --prod"
    npx --yes netlify-cli deploy $FLAGS ;;
  vercel)
    FLAGS="--name $NAME"; [ "$MODE" = prod ] && FLAGS="$FLAGS --prod"
    npx --yes vercel deploy dist $FLAGS ;;
  cloudflare)
    BRANCH="preview"; [ "$MODE" = prod ] && BRANCH="main"
    npx --yes wrangler pages deploy dist --project-name "$NAME" --branch "$BRANCH" ;;
  *) echo "DEPLOY_PROVIDER inválido: $PROVIDER"; exit 1 ;;
esac
