# Weather Monitoring Dashboard

A weather monitoring and forecast dashboard developed for the CDS212 DevOps module at FH Graubünden.

## Current Features

- FastAPI backend
- Current weather data from Open-Meteo
- Coordinate validation
- Automated tests with pytest
- Coverage and Ruff quality checks

## Setup

```bash
git clone git@github.com:Silivanili/weather-monitoring-dashboard.git
cd weather-monitoring-dashboard

python3.12 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Example request:

```bash
curl "http://127.0.0.1:8000/api/weather?latitude=46.85&longitude=9.53"
```

## API

### `GET /api/weather`

Returns current weather data for the supplied coordinates.

Required query parameters:

- `latitude`: -90 to 90
- `longitude`: -180 to 180

## Tests and Quality Checks

```bash
pytest -v
pytest --cov=app --cov-report=term-missing
ruff check .
ruff format --check .
```

## Project Status

Week 3: FastAPI foundation, weather API integration and automated tests.
