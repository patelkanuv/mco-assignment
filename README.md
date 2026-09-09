# MCO-Assignment

## Stack & Rationale
- I used Python, Flask, HTML/JavaScript, and SQLite (as specified in the assignment), with Docker/Compose for local orchestration. I'm already familiar with this stack, so I chose it to avoid a learning curve on React and Fastify while keeping the workflow simple and basic.
- Used docker-compose instead of Podman, just to reduce the learning curve of Podman.

## Architecture
- Divided the app into two basic parts: frontend and backend. Frontend is responsible for UI rendering, whereas backend handles all API requests.
- Frontend communicates with the backend over REST calls; CORS is enabled on the backend to allow this cross-origin access during local development.

## Running Locally
- Prerequisites: Docker and Docker Compose installed.
- `docker-compose up --build`
- Open http://localhost:5000 in a browser.

## CRUD Flow
- Allows full CRUD operations on stock inventory records — each entry has name, quantity, price, purchase date, and an optional category.
- The backend directory contains the code handling this (`app.py` for routes, `database.py` for persistence).

## Testing
- `pytest` or `pytest --cov` at the root of the repo will run the unit tests.
- CI runs these automatically.

## CI/CD (GitHub Actions)
- Backend: runs unit tests, then builds the backend Docker image (build only proceeds if tests pass).
- Frontend: builds the frontend Docker image.
- Reference: `.github/workflows/ci.yml`

## SDLC / Tooling / Engineering Practices
- On PR merge: "Automated testing" → `tests/` + CI job → build Docker image. (Deployment steps can be added later.)

## Path to Kubernetes
- **Replicas:** Frontend and backend are independent services. Both can be scaled through HPA (backend service, as of now, can't scale horizontally due to SQLite's single-writer file-based model).
- **Services:** Frontend talks to backend over its endpoint, passed as an env var — same pattern as docker-compose, but via a Kubernetes Service DNS name instead.
- **PVCs:** docker-compose uses a dedicated volume for SQLite for data retention; in Kubernetes this maps to a PersistentVolumeClaim mounted into the backend pod.
- **Secrets/Config:** In a prod environment, DB credentials would move to AWS Secrets Manager and be injected at pod runtime using the External Secrets Operator. 
- **Rolling updates:** Both services have health check endpoints for readiness/liveness. The frontend service is well-suited for rolling updates. Once the DB layer moves out of the backend (off SQLite), the backend would also become suitable for rolling updates.