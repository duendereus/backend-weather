# Fleet Investment Service

Microservicio de Rappi para calcular el nivel de inversión económica en flota en función de las condiciones climáticas de una región. Expone una API REST consumida por el frontend para determinar qué incentivo económico debe ofrecerse a los repartidores cuando el clima dificulta la operación.

---

## Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Requisitos previos](#requisitos-previos)
- [Configuración del entorno](#configuración-del-entorno)
- [Levantar el servicio localmente](#levantar-el-servicio-localmente)
- [Migraciones de base de datos](#migraciones-de-base-de-datos)
- [Endpoints de la API](#endpoints-de-la-api)
- [Lógica de incentivos](#lógica-de-incentivos)
- [Ejecutar tests](#ejecutar-tests)
- [Variables de entorno](#variables-de-entorno)
- [Estructura del proyecto](#estructura-del-proyecto)

---

## Arquitectura

El servicio sigue una arquitectura de capas desacopladas:

```
Frontend consumer
       │  HTTP
       ▼
  API Layer (FastAPI routers)
       │
  Service Layer (WeatherService · InvestmentService · SnapshotService)
       │
  Repository Layer (WeatherRepo · InvestmentRepo · ConfigRepo)
       │
  PostgreSQL
       
  APScheduler ──(scheduled)──► SnapshotService
```

La variable principal que determina el nivel de inversión en esta versión MVP es el **clima**, consultado en tiempo real contra [OpenWeatherMap](https://openweathermap.org/api). Los porcentajes de incentivo son configurables desde la base de datos sin necesidad de redeploy.

---

## Requisitos previos

- [Docker](https://docs.docker.com/get-docker/) >= 24
- [Docker Compose](https://docs.docker.com/compose/) >= 2.20
- Python 3.12+ (solo si quieres correr el proyecto fuera de Docker)
- Una API key de [OpenWeatherMap](https://home.openweathermap.org/users/sign_up) (plan gratuito es suficiente)

---

## Configuración del entorno

Copia el archivo de ejemplo y rellena tus valores:

```bash
cp .env.example .env
```

El campo obligatorio para arrancar es `OWM_API_KEY`. El resto tiene valores por defecto funcionales para desarrollo local. Ver la sección [Variables de entorno](#variables-de-entorno) para la referencia completa.

---

## Levantar el servicio localmente

```bash
# Construir imágenes y levantar todos los servicios
docker compose up --build

# En background
docker compose up --build -d

# Ver logs
docker compose logs -f api

# Apagar y eliminar volúmenes
docker compose down -v
```

La API quedará disponible en `http://localhost:8000`.  
La documentación interactiva (Swagger UI) en `http://localhost:8000/docs`.  
La documentación alternativa (ReDoc) en `http://localhost:8000/redoc`.

---

## Migraciones de base de datos

El proyecto usa [Alembic](https://alembic.sqlalchemy.org/) para gestionar el esquema de la base de datos.

```bash
# Crear una migración nueva (después de modificar modelos ORM)
docker compose exec api alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar migraciones pendientes
docker compose exec api alembic upgrade head

# Revertir la última migración
docker compose exec api alembic downgrade -1

# Ver el historial de migraciones
docker compose exec api alembic history
```

Las migraciones se aplican automáticamente al arrancar el contenedor en el entrypoint.

---

## Endpoints de la API

### Fleet — evaluación de inversión

```
POST /api/v1/fleet/evaluate
```

Solicita la evaluación del clima para una ubicación y devuelve el diagnóstico de inversión. Acepta ciudad por nombre o coordenadas.

```json
// Request por nombre de ciudad
{ "city": "Guadalajara" }

// Request por coordenadas
{ "lat": 20.659699, "lon": -103.349609 }

// Response
{
  "region": "Guadalajara",
  "condition": "RAIN",
  "description": "moderate rain",
  "temperature_c": 18.4,
  "wind_speed_ms": 3.2,
  "investment_level": "MEDIUM",
  "base_fare": 120.00,
  "incentive_pct": 35.0,
  "incentive_amt": 42.00,
  "total_investment": 162.00,
  "evaluated_at": "2024-11-15T14:32:00Z"
}
```

```
GET /api/v1/fleet/history
```

Historial de evaluaciones. Soporta paginación y filtros.

```
?region_id=uuid&from_date=2024-11-01&to_date=2024-11-30&limit=50&offset=0
```

---

### Config — incentivos configurables

```
GET  /api/v1/config/incentive
PUT  /api/v1/config/incentive/{condition}
```

Permite consultar y actualizar los porcentajes de incentivo por condición climática sin redeploy.

```json
// PUT /api/v1/config/incentive/RAIN
{ "base_fare": 120.00, "incentive_pct": 40.0 }
```

Las condiciones válidas son: `CLEAR`, `CLOUDS`, `DRIZZLE`, `RAIN`, `THUNDERSTORM`, `SNOW`, `EXTREME`.

---

### Regions — gestión de regiones

```
GET  /api/v1/regions
POST /api/v1/regions
GET  /api/v1/regions/{region_id}/snapshots
```

Registra ciudades o zonas geográficas a monitorear. Los snapshots periódicos los genera automáticamente el APScheduler.

---

## Lógica de incentivos

El incentivo es un porcentaje sobre la tarifa base, ambos configurables desde la DB:

| Condición climática OWM | Nivel de inversión | Incentivo por defecto |
|-------------------------|--------------------|-----------------------|
| CLEAR / CLOUDS          | NONE               | 0%                    |
| DRIZZLE                 | LOW                | 15%                   |
| RAIN                    | MEDIUM             | 35%                   |
| THUNDERSTORM / SNOW     | HIGH               | 60%                   |
| EXTREME                 | CRITICAL           | 100%                  |

```
total_investment = base_fare × (1 + incentive_pct / 100)
```

---

## Ejecutar tests

```bash
# Todos los tests (unit + integration)
docker compose --profile test run --rm test

# Solo tests unitarios (no requiere DB)
docker compose --profile test run --rm test pytest tests/unit -v

# Solo tests de integración
docker compose --profile test run --rm test pytest tests/integration -v

# Con reporte de cobertura
docker compose --profile test run --rm test pytest --cov=app --cov-report=term-missing

# Fuera de Docker (requiere DB corriendo y .env configurado)
pip install -e ".[dev]"
pytest -v
```

La cobertura mínima aceptada está configurada en `pyproject.toml`. El pipeline de CI rechazará PRs que bajen del umbral.

---

## Variables de entorno

| Variable                    | Requerida | Default                                        | Descripción                                     |
|-----------------------------|-----------|------------------------------------------------|-------------------------------------------------|
| `OWM_API_KEY`               | ✅        | —                                              | API key de OpenWeatherMap                       |
| `DATABASE_URL`              | ✅        | `postgresql://rappi:rappi@db:5432/fleet_invest`| Connection string de PostgreSQL                 |
| `OWM_BASE_URL`              | —         | `https://api.openweathermap.org/data/2.5`      | URL base de la API de OWM                       |
| `OWM_TIMEOUT_SECONDS`       | —         | `10`                                           | Timeout en segundos para llamadas a OWM         |
| `SNAPSHOT_INTERVAL_MINUTES` | —         | `15`                                           | Frecuencia del job de snapshots periódicos      |
| `LOG_LEVEL`                 | —         | `INFO`                                         | Nivel de logging (`DEBUG`, `INFO`, `WARNING`)   |
| `API_V1_PREFIX`             | —         | `/api/v1`                                      | Prefijo base de todos los endpoints             |
| `ENVIRONMENT`               | —         | `development`                                  | `development`, `staging`, `production`          |

---

## Estructura del proyecto

```
fleet-investment-service/
├── app/
│   ├── main.py                        # FastAPI app factory, lifespan events
│   ├── api/
│   │   ├── deps.py                    # Inyección de dependencias
│   │   └── v1/routers/
│   │       ├── fleet.py
│   │       ├── config.py
│   │       └── regions.py
│   ├── services/
│   │   ├── weather_service.py
│   │   ├── investment_service.py
│   │   └── snapshot_service.py
│   ├── repositories/
│   │   ├── weather_repository.py
│   │   ├── investment_repository.py
│   │   └── config_repository.py
│   ├── infrastructure/
│   │   ├── weather_client/
│   │   │   ├── base.py               # ABC — permite mock en tests
│   │   │   └── owm_client.py         # Implementación real contra OWM
│   │   ├── database.py
│   │   └── scheduler.py
│   ├── domain/
│   │   ├── enums.py
│   │   ├── models/                   # SQLAlchemy ORM
│   │   └── schemas/                  # Pydantic (request/response)
│   └── core/
│       ├── config.py                 # Settings con Pydantic BaseSettings
│       └── exceptions.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── alembic/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Contribución

1. Crea un branch desde `main` con la convención `feat/`, `fix/` o `chore/`.
2. Escribe el test primero (TDD). El pipeline valida que la cobertura no retroceda.
3. Corre `ruff check . && mypy app/` antes de abrir el PR.
4. Asegúrate de que `docker compose --profile test run --rm test` pase en verde localmente.
