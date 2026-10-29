# helloPadelDashboard

Dashboard interno de Hello Padel Academy: to-dos, notas, tiempo y, más adelante, inventario, calendario y métricas de redes.

- **Backend:** FastAPI + SQLAlchemy 2 (async) + Alembic + PostgreSQL (`backend/`)
- **Frontend:** React + Vite + TypeScript + Tailwind (`frontend/`, próximamente)

## Arrancar

```bash
cp .env.example .env
docker compose up --build
```

Las migraciones se aplican solas al arrancar el backend.

- API: http://localhost:8000/api
- Documentación interactiva: http://localhost:8000/api/docs
- Postgres en el host: `localhost:5433` (configurable con `DB_PORT`)

## Crear el primer admin

Con los servicios levantados:

```bash
docker compose exec backend python -m app.cli create-admin
```

Te pedirá email, nombre y contraseña (mínimo 8 caracteres). También acepta `--email`, `--name` y `--password`. El resto de cuentas las crea un admin desde el dashboard (`POST /api/users`).

## Tests

```bash
docker compose run --rm backend pytest
```

Usan una base de datos aparte (`<POSTGRES_DB>_test`) que se crea automáticamente.

Lint y formato:

```bash
docker compose run --rm --no-deps backend sh -c "ruff check . && ruff format --check ."
```

## Migraciones

```bash
docker compose exec backend alembic revision --autogenerate -m "descripción"
docker compose exec backend alembic upgrade head
```

Al crear un módulo nuevo, importa sus modelos en `backend/app/models.py` para que Alembic los detecte.

## Estructura del backend

```
backend/app/
├── core/       # config, BD, seguridad (JWT, argon2), dependencias, errores
├── shared/     # Base de modelos, mixins, enums y tipos comunes
├── modules/    # un paquete por dominio: models, schemas, service, router
│   ├── auth/
│   ├── users/
│   └── todos/
├── models.py   # registro de modelos para Alembic
├── cli.py      # comandos de gestión
└── main.py
```

## Permisos

- Lo **personal** (to-dos, notas) solo lo ve y lo modifica su dueño, admin incluido. A los demás les devuelve 404.
- **To-dos de empresa:** todos los ven y pueden marcarlos como hechos. Editar o borrar: creador, persona asignada o admin.

## Autenticación

- `POST /api/auth/login` devuelve un access token (15 min) y guarda el refresh token (7 días) en una cookie `httpOnly` limitada a `/api/auth`.
- `POST /api/auth/refresh` rota el refresh token. Si se reutiliza un token ya rotado (fuera de una ventana de 30 s para pestañas simultáneas), se cierran todas las sesiones del usuario.
- `POST /api/auth/logout` revoca el refresh token.
- Desactivar un usuario o resetear su contraseña cierra todas sus sesiones.
