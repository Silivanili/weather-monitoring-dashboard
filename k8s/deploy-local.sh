#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

NAMESPACE="weather-dashboard"
IMAGE="weather-dashboard:k8s-v1"
CONTEXT="kind-weather-dashboard"

echo "===== KONTEXT PRUEFEN ====="
if [[ "$(kubectl config current-context)" != "$CONTEXT" ]]; then
  echo "Falscher Kubernetes-Kontext. Abbruch."
  exit 1
fi

echo "===== NAMESPACE ====="
kubectl apply -f k8s/00-namespace.yaml

echo "===== DATENBANK-SECRET ====="
if kubectl -n "$NAMESPACE" get secret weather-db-credentials \
    >/dev/null 2>&1; then
  echo "Vorhandenes Secret wird beibehalten."
else
  umask 077
  secret_file=$(mktemp /dev/shm/weather-db.XXXXXX)
  trap 'rm -f "$secret_file"' EXIT

  {
    printf 'POSTGRES_USER=weather_app\n'
    printf 'POSTGRES_DB=weather_dashboard\n'
    printf 'POSTGRES_PASSWORD='
    openssl rand -hex 24
  } > "$secret_file"

  kubectl -n "$NAMESPACE" create secret generic \
    weather-db-credentials \
    --from-env-file="$secret_file"

  rm -f "$secret_file"
fi

echo "===== POSTGRESQL ====="
kubectl apply -f k8s/10-postgres.yaml

kubectl -n "$NAMESPACE" rollout status \
  statefulset/weather-postgres --timeout=180s

echo "===== DOCKER-IMAGE ====="
docker image inspect "$IMAGE" >/dev/null
kind load docker-image "$IMAGE" --name weather-dashboard

echo "===== KUBERNETES-MANIFESTE ====="
kubectl apply -f k8s/

kubectl -n "$NAMESPACE" rollout status \
  deployment/weather-web --timeout=180s

echo "===== ERGEBNIS ====="
kubectl -n "$NAMESPACE" get pods -o wide

echo "===== HTTP-TEST ====="
curl --fail --silent --show-error \
  http://127.0.0.1:30080/ready

echo
echo "Deployment erfolgreich."
