# Kubernetes Deployment

Complete manifests for deploying the orbital tracker on Kubernetes. Production runs on EC2 rather than EKS because the EKS control plane costs ~$73/month regardless of workload, not worth it for a project at this scale. The manifests are here for portability and were validated end-to-end on minikube.

The frontend isn't included, it's a static React build that belongs on a CDN, not in a cluster.

---

## What's Here

- `namespace.yaml` — isolates everything under `orbital-tracker`
- `configmap.yaml` — environment config the backend reads on startup
- `postgres.yaml` — in-cluster Postgres with a PVC (production would use RDS)
- `redis.yaml` — in-cluster Redis (production would use a managed equivalent)
- `migrate-job.yaml` — runs `alembic upgrade head` once before the backend starts
- `backend.yaml` — FastAPI deployment with 2 replicas, a ClusterIP service, and an HPA
- `position-service.yaml` — Java SGP4 microservice with 2 replicas, a ClusterIP service, and an HPA
- `ingress.yaml` — NGINX ingress routing external traffic to the backend

---

## Notes

The Dockerfile runs `alembic upgrade head && uvicorn ...` as its start command, which works fine for `docker compose` with a single container. In Kubernetes with multiple replicas, every pod would race to run migrations on startup. The backend manifest overrides that command to run uvicorn only, and the migration Job handles the schema upgrade once before the backend rolls out.

The HPA scales the backend between 2 and 10 replicas based on CPU utilization. CPU is the right signal here because SGP4 propagation is CPU-bound, concurrent position requests drive CPU up, which triggers scale-out.

The position service (the Java SGP4 microservice) has its own HPA and scales independently of the backend. That independent scaling is the main reason the computation was split into its own service, the CPU-bound work can scale separately from the request-handling layer.

Postgres and Redis run in-cluster here purely for validation. Running stateful databases inside a cluster adds operational overhead that isn't worth it for this project.

---

## Running on Minikube

```bash
# start the cluster with enough resources
minikube start --memory=3072 --cpus=2
minikube addons enable ingress
minikube addons enable metrics-server

# build both images inside minikube's docker daemon
minikube image build -t orbital-tracker-backend:local .
minikube image build -t orbital-tracker-position-service:local services/position-service

# apply in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml

# wait for postgres before running migrations
kubectl wait --for=condition=ready pod -l component=postgres -n orbital-tracker --timeout=120s

kubectl apply -f k8s/migrate-job.yaml
kubectl wait --for=condition=complete job/alembic-migrate -n orbital-tracker --timeout=120s

kubectl apply -f k8s/position-service.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/ingress.yaml
```

Verify everything came up:

```bash
kubectl get all -n orbital-tracker
kubectl get hpa -n orbital-tracker
```

The ingress IP is whatever `kubectl get ingress -n orbital-tracker` shows under ADDRESS. On Linux with minikube's Docker driver you can curl it directly:

```bash
curl http://<ingress-address>/health
```

If that doesn't work, port-forward directly to the service:

```bash
kubectl port-forward -n orbital-tracker svc/backend-service 8080:80
curl http://localhost:8080/health
```

Useful for debugging if pods aren't coming up:

```bash
kubectl logs -n orbital-tracker deploy/orbital-tracker-backend
kubectl logs -n orbital-tracker job/alembic-migrate
kubectl describe pod -n orbital-tracker -l component=backend
```

---

