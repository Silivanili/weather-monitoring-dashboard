# Weather Monitoring Dashboard

A self-hosted weather monitoring and forecast dashboard developed for the CDS212 DevOps module at the University of Applied Sciences of the Grisons (FH Graubünden).

The project combines weather data integration, a FastAPI backend, PostgreSQL persistence, automated testing, and containerized deployment.

**Live Demo:** [weather.silivanili.duckdns.org](https://weather.silivanili.duckdns.org)

## Features

- Web-based weather dashboard
- Current weather data and forecasts from Open-Meteo
- Location search and coordinate validation
- REST API built with FastAPI
- PostgreSQL database integration
- Docker Compose deployment
- Application health and database readiness endpoints
- Automated tests with pytest
- Coverage checks and Ruff linting
- Public HTTPS deployment using Nginx Proxy Manager and DuckDNS

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3.12, FastAPI |
| Frontend | HTML, CSS, Jinja2 |
| Database | PostgreSQL 16, SQLAlchemy |
| Weather data | Open-Meteo |
| Containerization | Docker, Docker Compose |
| Reverse proxy | Nginx Proxy Manager |
| DNS / HTTPS | DuckDNS, Let's Encrypt |
| Testing | pytest, pytest-cov |
| Code quality | Ruff |
| Version control | Git, GitHub |
| Infrastructure as Code | Terraform, kreuzwerker/docker |

## Local Development

### Prerequisites

- Python 3.12 or newer
- Git

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/Silivanili/weather-monitoring-dashboard.git
cd weather-monitoring-dashboard

python3.12 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

### Run the Application

```bash
uvicorn app.main:app --reload --port 8000
```

Open the dashboard at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

## Docker Compose

Docker Compose runs the FastAPI application and PostgreSQL in separate containers.

### Prerequisites

- Docker Engine
- Docker Compose v2


### Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and replace both password placeholders with
different, secure passwords.

Generate secure passwords, for example, using:

```bash
openssl rand -hex 24
```

The required environment variables are:

| Variable | Description |
|---|---|
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `GRAFANA_ADMIN_PASSWORD` | Grafana administrator password |

**Security:**
- Never commit `.env` or real credentials to Git.
- Use different passwords for PostgreSQL and Grafana.
- `.env.example` contains placeholders only and is safe to commit.



### Start the Containers

```bash
docker compose up -d --build
```

Check the container status:

```bash
docker compose ps
```

Verify the application:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Open the dashboard at http://localhost:8000.

Stop the containers:

```bash
docker compose down
```

PostgreSQL data is stored in a persistent Docker volume and is preserved when the containers are stopped or recreated. The Docker volume is not a substitute for a backup.

## Infrastructure as Code (Terraform)

The project includes a Terraform configuration using the `kreuzwerker/docker` provider.

It manages a local Docker image reference and a FastAPI container, demonstrating declarative infrastructure provisioning, variable validation, outputs, state management, idempotency, and configuration drift detection.

### Quick Start

From the project root:

```bash
docker build -t weather-dashboard:terraform-local .
cd terraform
terraform init
terraform validate
terraform plan
terraform apply
```

The dashboard is available at http://localhost:18080.

To remove the Terraform-managed infrastructure:

```bash
terraform destroy
```

This deployment runs separately from the Docker Compose stack. It uses an in-memory SQLite database and is intended for local testing and demonstrating Infrastructure as Code, not for persistent production deployment.

For configuration variables, outputs, verification results, and further details, see [Terraform Documentation](terraform/README.md).

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Web dashboard |
| GET | `/api/weather` | Current weather conditions |
| GET | `/api/weather/forecast` | Weather forecast |
| GET | `/api/locations/search` | Location search |
| GET | `/health` | Application health |
| GET | `/ready` | Database readiness |

### Example Request

```bash
curl "http://127.0.0.1:8000/api/weather?latitude=46.85&longitude=9.53"
```

The API validates coordinates:

- `latitude`: -90 to 90
- `longitude`: -180 to 180

The interactive API documentation is available at `/docs`.

## Deployment

The application is currently self-hosted on an Ubuntu Linux server.

The deployment architecture consists of:

1. DuckDNS resolves the public dashboard hostname.
2. Nginx Proxy Manager terminates HTTPS connections using a Let's Encrypt certificate.
3. The reverse proxy forwards requests to the FastAPI container.
4. FastAPI accesses PostgreSQL through the internal Docker Compose network.

**Public URL:** https://weather.silivanili.duckdns.org

The PostgreSQL container does not publish its database port to the host. Database credentials are provided through local environment configuration.

## Tests and Quality Checks

Install development dependencies before running the checks.

```bash
pytest -v
pytest --cov=app --cov-report=term-missing
ruff check .
ruff format --check .
```

The project includes automated tests for weather services, weather forecasts, location services, API endpoints, and readiness checks.

## Development Workflow

This project follows **GitHub Flow**.

Development takes place on short-lived feature or fix branches. Changes are integrated into `main` through Pull Requests.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete branching and contribution rules.

## Project Status

The project is actively being developed as part of the CDS212 DevOps module.

Implemented functionality includes weather data integration, forecasting, location search, database persistence, automated testing, and a containerized public deployment.

### Planned Improvements

- API rate limiting
- Additional deployment and integration tests
- Automated deployment workflow
- Improved production security and resource management
- Further weather monitoring and analysis capabilities

## License

See [LICENSE](LICENSE) for licensing information.
