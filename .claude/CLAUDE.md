# CLAUDE.md — Fleet Investment Service

Este archivo le indica a Claude cómo trabajar en este repositorio. Léelo completo antes de escribir cualquier línea de código o modificar archivos existentes.

---

## Contexto del proyecto

Microservicio de **Rappi** que determina el nivel de inversión económica en flota de repartidores en función del clima de una región. El resultado se expone vía API REST para que el frontend lo consuma. En el MVP, la única variable que determina la inversión es el clima (OpenWeatherMap). La lógica de incentivos consiste en aplicar un porcentaje configurable sobre una tarifa base cuando las condiciones climáticas son adversas para el delivery.

---

## Stack tecnológico

- **Runtime:** Python 3.12
- **Framework:** FastAPI con Uvicorn
- **Base de datos:** PostgreSQL 16 + SQLAlchemy 2 (async) + Alembic
- **Validación:** Pydantic v2
- **Cliente HTTP:** httpx (async)
- **Scheduler:** APScheduler 3.x
- **Testing:** pytest + pytest-asyncio + httpx (TestClient) + pytest-cov
- **Linting/Typing:** ruff + mypy
- **Contenerización:** Docker + Docker Compose

---

## Principios de desarrollo obligatorios

### TDD (Test-Driven Development)

Siempre escribe el test antes que la implementación. El flujo es:

1. Escribir el test que describe el comportamiento esperado → el test falla (red).
2. Escribir el mínimo código necesario para que pase (green).
3. Refactorizar sin romper tests (refactor).

No agregues ni modifiques lógica de negocio sin un test que la respalde.

### DRY (Don't Repeat Yourself)

- Si la misma lógica aparece dos veces, extráela a una función o clase compartida.
- Los schemas de Pydantic se definen una sola vez en `app/domain/schemas/`. No dupliques campos entre request y response schemas si pueden heredar de una base común.
- Las queries SQL complejas y reutilizables van en el repositorio, no en el servicio.
- Las constantes y enums van en `app/domain/enums.py`. Nunca uses strings mágicos como `"RAIN"` fuera de ese archivo.

---

## Arquitectura y reglas por capa

### API Layer (`app/api/`)

- Los routers **no contienen lógica de negocio**. Solo validan el request (Pydantic hace eso automáticamente), llaman al servicio correspondiente y devuelven el response.
- Las dependencias (sesión de DB, instancias de services) se inyectan siempre vía `Depends()` desde `app/api/deps.py`.
- Nunca importes un repositorio directamente en un router. Los routers solo conocen services.
- Los status codes HTTP deben ser semánticamente correctos: `201` para creación, `200` para consulta, `422` para validación, `404` para not found, `503` cuando OWM no responde.

### Service Layer (`app/services/`)

- Los services contienen toda la lógica de negocio.
- Un service puede llamar a otro service si el flujo lo requiere (por ejemplo, `InvestmentService` puede usar `WeatherService` internamente).
- Los services **nunca acceden a la DB directamente**. Solo usan repositorios.
- Los services **nunca hacen HTTP directamente**. Solo usan el `WeatherClient` (inyectado).
- Las excepciones de dominio (`WeatherServiceUnavailableError`, `RegionNotFoundError`, etc.) se lanzan desde los services y se capturan en los exception handlers de FastAPI definidos en `main.py`.

### Repository Layer (`app/repositories/`)

- Un repositorio por entidad principal de la DB.
- Los métodos de repositorio deben tener nombres con intención clara: `get_by_region_id`, `save_evaluation`, `get_latest_snapshot`, no `select`, `insert`, `query`.
- Nunca filtres, transformes ni calcules datos en el repositorio. Solo persiste y recupera.
- Usa siempre la sesión async de SQLAlchemy. No mezcles sync/async.

### Infrastructure (`app/infrastructure/`)

- `WeatherClient` es una ABC en `base.py`. La implementación real (`OWMClient`) y los fakes de test implementan esa interfaz. Nunca dependas de `OWMClient` directamente fuera de `infrastructure/`. Depende siempre de la ABC.
- El scheduler se inicializa en el lifespan de FastAPI (`main.py`), no en un módulo al importarse.

### Domain (`app/domain/`)

- Los **modelos ORM** (`app/domain/models/`) representan las tablas. No pongas lógica de negocio aquí.
- Los **schemas Pydantic** (`app/domain/schemas/`) son los contratos de la API. Separa claramente los schemas de request, response e internos.
- Los **enums** (`app/domain/enums.py`) son la fuente de verdad para `WeatherCondition`, `InvestmentLevel`, etc.

---

## Convenciones de código

### Naming

- Clases en `PascalCase`. Funciones, variables y archivos en `snake_case`.
- Los repositorios terminan en `Repository`, los services en `Service`, los schemas en `Request`/`Response`/`Schema`.
- Los tests siguen el patrón `test_<función_o_comportamiento>_<condición>`. Ejemplo: `test_calculate_investment_returns_high_level_on_thunderstorm`.

### Async

Todas las funciones que hacen I/O (DB, HTTP) deben ser `async`. No mezcles `asyncio.run()` dentro de código async.

### Imports

Ordena los imports en tres grupos separados por línea en blanco: stdlib → third-party → internal. Ruff lo valida automáticamente.

### Type hints

Todo el código debe tener type hints completos. `mypy` corre en el pipeline y rechaza errores de tipado. Nunca uses `Any` salvo que sea estrictamente inevitable y documentes el porqué.

### Excepciones

Define excepciones de dominio custom en `app/core/exceptions.py`. Nunca uses `Exception` genérico para errores de negocio. Nunca silencies excepciones con `except: pass`.

---

## Cómo correr el proyecto

```bash
# Levantar todo (API + DB)
docker compose up --build

# Aplicar migraciones
docker compose exec api alembic upgrade head

# Crear migración nueva tras modificar modelos ORM
docker compose exec api alembic revision --autogenerate -m "descripcion"

# Correr todos los tests
docker compose --profile test run --rm test

# Solo tests unitarios (rápidos, sin DB)
docker compose --profile test run --rm test pytest tests/unit -v

# Cobertura
docker compose --profile test run --rm test pytest --cov=app --cov-report=term-missing

# Linting y tipos
docker compose exec api ruff check .
docker compose exec api mypy app/
```

---

## Cómo correr tests fuera de Docker

```bash
pip install -e ".[dev]"
export DATABASE_URL="postgresql+asyncpg://rappi:rappi@localhost:5432/fleet_invest_test"
export OWM_API_KEY="fake-key-for-unit-tests"
pytest tests/unit -v                  # no necesita DB
pytest tests/integration -v           # necesita DB de test corriendo
```

---

## Estructura de un test unitario de service

Los tests unitarios de services usan fakes inyectados, nunca mocks mágicos de librerías. La razón es que los fakes son más legibles y reflejan el contrato de las interfaces reales.

```python
# tests/unit/test_investment_service.py

from app.services.investment_service import InvestmentService
from app.domain.enums import WeatherCondition, InvestmentLevel
from tests.fakes import FakeInvestmentRepository, FakeConfigRepository

async def test_calculate_returns_medium_level_on_rain():
    config_repo = FakeConfigRepository(
        incentive_pct_by_condition={WeatherCondition.RAIN: 35.0},
        base_fare=120.00,
    )
    investment_repo = FakeInvestmentRepository()
    service = InvestmentService(
        investment_repo=investment_repo,
        config_repo=config_repo,
    )

    result = await service.calculate(
        condition=WeatherCondition.RAIN,
        region_id="some-uuid",
        query_log_id="some-log-uuid",
    )

    assert result.investment_level == InvestmentLevel.MEDIUM
    assert result.incentive_pct == 35.0
    assert result.total_investment == 162.00  # 120 * 1.35
```

---

## Estructura de un test de integración

```python
# tests/integration/test_fleet_router.py

import pytest
from httpx import AsyncClient
from tests.fixtures import override_weather_client

async def test_evaluate_returns_investment_for_rainy_city(
    client: AsyncClient,
    override_weather_client,  # fixture que reemplaza OWMClient con un fake
):
    response = await client.post(
        "/api/v1/fleet/evaluate",
        json={"city": "Guadalajara"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["condition"] == "RAIN"
    assert data["investment_level"] == "MEDIUM"
    assert data["total_investment"] > data["base_fare"]
```

---

## Qué NO hacer

- No escribas lógica de negocio en routers o repositorios.
- No hardcodees strings de condición climática (`"RAIN"`, `"STORM"`) fuera de `enums.py`.
- No hagas llamadas HTTP reales en ningún test. Siempre usa un fake o el `respx` mocker.
- No uses `time.sleep()` en tests. Usa `freezegun` o controla el tiempo con fixtures.
- No uses `print()` para debugging. Usa el logger del módulo (`logger = logging.getLogger(__name__)`).
- No agregues dependencias al proyecto sin actualizar `pyproject.toml` y justificarlo en el PR.
- No apliques migraciones manualmente con SQL directo. Siempre vía Alembic.
- No ignores errores de `mypy` o `ruff` con comentarios `# type: ignore` o `# noqa` sin una razón documentada en el mismo comentario.
- No expongas el `DATABASE_URL` con credenciales reales en ningún archivo commiteado. Usa `.env` (está en `.gitignore`).

---

## Flujo al agregar un feature nuevo

1. Identifica si el cambio requiere una migración de DB. Si sí, modifica el modelo ORM primero.
2. Escribe el test unitario del service (falla).
3. Implementa el cambio en el service (pasa).
4. Agrega o ajusta el repositorio si el test de integración lo requiere.
5. Conecta el endpoint en el router.
6. Escribe el test de integración del router.
7. Corre `ruff check . && mypy app/ && pytest` en verde antes de commitear.

---

## Flujo al modificar la lógica de incentivos

La lógica de mapeo `WeatherCondition → InvestmentLevel` vive en `InvestmentService`. Los porcentajes son datos de la DB (`incentive_config`). Si agregas un nuevo nivel o condición:

1. Agrega el valor al enum en `app/domain/enums.py`.
2. Crea la migración Alembic para insertar el nuevo registro en `incentive_config`.
3. Actualiza `InvestmentService` si el mapeo de nivel cambia.
4. Actualiza los tests unitarios correspondientes.

No toques los porcentajes directamente en el código fuente. Van en la DB o en el seed de datos de la migración.

---

## Cobertura mínima

| Módulo          | Cobertura mínima |
|-----------------|------------------|
| `services/`     | 90%              |
| `repositories/` | 80%              |
| `api/routers/`  | 70%              |
| `domain/`       | 85%              |

El pipeline de CI falla si la cobertura global baja del **85%**.
