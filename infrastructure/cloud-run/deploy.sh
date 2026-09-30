#!/usr/bin/env bash
# Repeatable deploy of TatRaksha to Cloud Run (asia-south1): API + both Next.js dashboards.
#
#   infrastructure/cloud-run/deploy.sh            # all three services
#   infrastructure/cloud-run/deploy.sh api        # just the API (also: district-dashboard, state-eoc-dashboard)
#
# Images are built by Cloud Build from the repo root (the API needs ai/, data/, geospatial/ at runtime) and pushed
# to Artifact Registry. Secrets come from Secret Manager; nothing secret is written to git.
#
# Gemini: runs on Vertex AI with the service account (no key needed) unless USE_VERTEX_GEMINI=false.
# Once the lead creates the secret  `gcloud secrets create gemini-api-key --data-file=-`  this script also
# attaches GEMINI_API_KEY=gemini-api-key:latest automatically (used when USE_VERTEX_GEMINI=false).
#
# Browser Maps key: NEXT_PUBLIC_MAPS_API_KEY from the environment, else apps/<app>/.env.local. It is baked into
# the JS bundle at build time via a generated, gitignored apps/<app>/.env.production that is uploaded to Cloud
# Build (see .gcloudignore) and deleted afterwards. Restrict that key by HTTP referrer (https://*.run.app).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-asia-south1}"
SA="${SERVICE_ACCOUNT:-hackathon-dev@${PROJECT}.iam.gserviceaccount.com}"
AR_REPO="${AR_REPO:-cloud-run-source-deploy}"
PREFIX="cyclone-risk-network"
BIGQUERY_DATASET="${BIGQUERY_DATASET:-cyclone_risk_network}"
GCS_BUCKET="${GCS_BUCKET:-${PROJECT}-media}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.7-flash}"
GEMINI_LOCATION="${GEMINI_LOCATION:-global}"
USE_VERTEX_GEMINI="${USE_VERTEX_GEMINI:-true}"
# Opt-in once set up: Earth Engine registration / Firestore database
EARTH_ENGINE_PROJECT="${EARTH_ENGINE_PROJECT:-}"
FIREBASE_PROJECT_ID="${FIREBASE_PROJECT_ID:-}"
TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
TARGETS=("${@:-api district-dashboard state-eoc-dashboard}")
TARGETS=(${TARGETS[*]})

: "${PROJECT:?set GOOGLE_CLOUD_PROJECT or gcloud config set project}"
NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
url_of() { echo "https://$1-${NUMBER}.${REGION}.run.app"; }   # deterministic Cloud Run URL
API_URL="$(url_of "${PREFIX}-api")"
DISTRICT_URL="$(url_of "${PREFIX}-district-dashboard")"
STATE_URL="$(url_of "${PREFIX}-state-eoc-dashboard")"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT}/${AR_REPO}"

if ! gcloud artifacts repositories describe "$AR_REPO" --project "$PROJECT" --location "$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$AR_REPO" --project "$PROJECT" --location "$REGION" \
    --repository-format docker --description "Cloud Run images"
fi

secret_exists() { gcloud secrets describe "$1" --project "$PROJECT" >/dev/null 2>&1; }

build() {  # build <image-name> <dockerfile> [app]
  local image="${REGISTRY}/${PREFIX}-$1:${TAG}"
  gcloud builds submit "$ROOT" --project "$PROJECT" --region "$REGION" --quiet \
    --config infrastructure/cloud-run/cloudbuild.yaml \
    --substitutions "_IMAGE=${image},_DOCKERFILE=$2,_APP=${3:-}" >&2
  echo "$image"
}

deploy_api() {
  local image secrets env
  image="$(build api services/api/Dockerfile)"
  secrets="MAPS_API_KEY=maps-api-key:latest,GOOGLE_CLOUD_API_KEY=google-api-key:latest"
  if secret_exists gemini-api-key; then secrets+=",GEMINI_API_KEY=gemini-api-key:latest"; fi
  env="GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION},GEMINI_LOCATION=${GEMINI_LOCATION}"
  env+=",GEMINI_MODEL=${GEMINI_MODEL},GOOGLE_GENAI_USE_VERTEXAI=${USE_VERTEX_GEMINI}"
  env+=",BIGQUERY_DATASET=${BIGQUERY_DATASET},GCS_BUCKET=${GCS_BUCKET}"
  env+=",EARTH_ENGINE_PROJECT=${EARTH_ENGINE_PROJECT},FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}"
  env+=",CORS_ORIGINS=${DISTRICT_URL};${STATE_URL};http://localhost:3050;http://localhost:3051"
  # max-instances=1: without Firestore the record store is per-instance SQLite, so keep one instance for the demo.
  gcloud run deploy "${PREFIX}-api" --project "$PROJECT" --region "$REGION" --image "$image" \
    --service-account "$SA" --allow-unauthenticated --port 8080 \
    --cpu 1 --memory 1Gi --timeout 300 --concurrency 40 --min-instances 0 --max-instances 1 --cpu-boost \
    --set-env-vars "^@^$(echo "$env" | tr ',' '@' | sed 's/;/,/g')" --set-secrets "$secrets" \
    --labels "app=${PREFIX},component=api"
}

deploy_web() {  # deploy_web <app folder>
  local app="$1" key image envfile="apps/$1/.env.production"
  key="${NEXT_PUBLIC_MAPS_API_KEY:-$(grep -s '^NEXT_PUBLIC_MAPS_API_KEY=' "apps/${app}/.env.local" | cut -d= -f2- || true)}"
  trap 'rm -f "$envfile"' RETURN
  printf 'NEXT_PUBLIC_API_URL=%s\nNEXT_PUBLIC_MAPS_API_KEY=%s\n' "$API_URL" "$key" > "$envfile"
  image="$(build "$app" infrastructure/cloud-run/Dockerfile.web "$app")"
  gcloud run deploy "${PREFIX}-${app}" --project "$PROJECT" --region "$REGION" --image "$image" \
    --service-account "$SA" --allow-unauthenticated --port 8080 \
    --cpu 1 --memory 512Mi --min-instances 0 --max-instances 3 --cpu-boost \
    --labels "app=${PREFIX},component=${app}"
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    api) deploy_api ;;
    district-dashboard|state-eoc-dashboard) deploy_web "$t" ;;
    *) echo "unknown target $t" >&2; exit 2 ;;
  esac
done

echo
echo "API:                 ${API_URL}   (health: ${API_URL}/health, status: ${API_URL}/api/status)"
echo "District dashboard:  ${DISTRICT_URL}"
echo "State EOC dashboard: ${STATE_URL}"
