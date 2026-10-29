# helloPadelDashboard

Dashboard interno de Hello Padel Academy: to-dos, notas, tiempo y, más adelante, inventario, calendario y métricas de redes.

- **Backend:** FastAPI + SQLAlchemy 2 (async) + Alembic + PostgreSQL (`backend/`)
- **Frontend:** React + Vite + TypeScript + Tailwind (`frontend/`)

## Arrancar

```bash
cp .env.example .env
docker compose up --build
```

Las migraciones se aplican solas al arrancar el backend.

- Dashboard: http://localhost:5173
- API: http://localhost:8000/api
- Documentación interactiva: http://localhost:8000/api/docs
- Postgres en el host: `localhost:5433` (configurable con `DB_PORT`)

## Crear el primer admin

Con los servicios levantados:

```bash
docker compose exec backend python -m app.cli create-admin
```

Te pedirá email, nombre y contraseña (mínimo 8 caracteres). También acepta `--email`, `--name` y `--password`. El resto de cuentas las crea un admin desde el dashboard (`POST /api/users`).

## Datos de ejemplo (opcional, solo desarrollo)

```bash
docker compose exec backend python -m app.cli seed
```

Crea tres usuarios con tareas y notas de ejemplo: `admin@example.com` (admin), `ana@example.com` y `bruno@example.com` (equipo). Todos usan la contraseña `hellopadel-dev`. Si ya existen, no hace nada. No se puede ejecutar con `ENVIRONMENT=production`.

## Tests

```bash
docker compose run --rm backend pytest
```

Usan una base de datos aparte (`<POSTGRES_DB>_test`) que se crea automáticamente.

Lint y formato:

```bash
docker compose run --rm --no-deps backend sh -c "ruff check . && ruff format --check ."
```

Typecheck y build del frontend:

```bash
docker compose exec frontend npm run build
```

## Migraciones

```bash
docker compose exec backend alembic revision --autogenerate -m "descripción"
docker compose exec backend alembic upgrade head
```

Al crear un módulo nuevo, importa sus modelos en `backend/app/models.py` para que Alembic los detecte.

Para comprobar que las migraciones coinciden con los modelos (los tests crean las tablas directamente desde los modelos, así que no lo detectan):

```bash
docker compose exec backend alembic check
```

## Estructura del backend

```
backend/app/
├── core/       # config, BD, seguridad (JWT, argon2), dependencias, errores
├── shared/     # Base de modelos, mixins, enums y tipos comunes
├── modules/    # un paquete por dominio: models, schemas, service, router
│   ├── auth/
│   ├── users/
│   ├── todos/
│   ├── notes/
│   ├── weather/
│   ├── home/
│   ├── campuses/
│   ├── events/
│   ├── inventory/
│   └── shipments/
├── models.py   # registro de modelos para Alembic
├── cli.py      # comandos de gestión
└── main.py
```

## Estructura del frontend

```
frontend/src/
├── api/          # cliente fetch (refresh automático), endpoints, tipos y hooks de TanStack Query
├── auth/         # AuthContext y guards de rutas
├── components/   # layout (sidebar, navegación) y UI básica
├── features/     # una carpeta por sección: home, events, shipments, inventory, campuses,
│                 #   todos, notes, users, account, login
└── lib/          # formato de fechas, utilidades
```

Para añadir una sección: crea su carpeta en `features/`, añade la ruta en `App.tsx` y el enlace en `components/layout/navigation.ts`.

Si cambias dependencias del frontend, recrea su volumen de `node_modules`:

```bash
docker compose up -d --build --renew-anon-volumes frontend
```

## Permisos

- Lo **personal** (to-dos, notas) solo lo ve y lo modifica su dueño, admin incluido. A los demás les devuelve 404.
- **To-dos de empresa:** todos los ven y pueden marcarlos como hechos. Editar o borrar: creador, persona asignada o admin.
- **Notas de empresa:** todos las leen. Editar o borrar: el autor o un admin. El contenido es markdown y el ámbito de una nota no se puede cambiar.

## Home

`GET /api/home` devuelve en una sola llamada el resumen de la pantalla principal: las 5 primeras tareas pendientes personales y de empresa, los contadores (pendientes, asignadas a ti, vencidas) y las 4 últimas notas que puedes ver. "Vencida" se calcula con la fecha de `TIMEZONE` (por defecto `Europe/Madrid`). El tiempo se pide aparte, con la ubicación del navegador; si no hay permiso, usa Barcelona.

## Tiempo

`GET /api/weather?lat=&lon=` (sin coordenadas usa Barcelona) consulta Open-Meteo, sin API key, desde el backend. La respuesta se guarda en caché 15 min por coordenadas redondeadas a ~1 km (`WEATHER_CACHE_TTL_SECONDS`). Si Open-Meteo falla, sirve el último dato guardado marcado con `stale: true`. La caché vive en memoria: si se despliegan varias réplicas, habrá que cambiarla por Redis (`app/core/cache.py`).

## Autenticación

- `POST /api/auth/login` devuelve un access token (15 min) y guarda el refresh token (7 días) en una cookie `httpOnly` limitada a `/api/auth`.
- `POST /api/auth/refresh` rota el refresh token. Si se reutiliza un token ya rotado (fuera de una ventana de 30 s para pestañas simultáneas), se cierran todas las sesiones del usuario.
- `POST /api/auth/logout` revoca el refresh token.
- Desactivar un usuario o resetear su contraseña cierra todas sus sesiones.

## Despliegue: frontend en GitHub Pages

El frontend se publica en `https://josep-teruel-surra.github.io/helloPadelDashboard/` con el workflow `.github/workflows/pages.yml`, que se lanza en cada push a `main` que toque `frontend/`. **El backend y Postgres van aparte**: GitHub Pages solo sirve archivos estáticos.

### 1. Backend (en cualquier servidor con HTTPS)

Imagen `backend/Dockerfile` (`--build-arg INSTALL_DEV=false`) más un Postgres. Variables mínimas:

```
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://usuario:contraseña@host:5432/hellopadel
JWT_SECRET=<openssl rand -hex 32>
COOKIE_SECURE=true
COOKIE_SAMESITE=none
CORS_ORIGINS=https://josep-teruel-surra.github.io
```

Al arrancar aplica las migraciones. Después, crea el primer admin con `python -m app.cli create-admin`.

### 2. GitHub

1. Settings → Pages → Source: **GitHub Actions**.
2. Settings → Secrets and variables → Actions → Variables: `API_URL` = URL del backend (p. ej. `https://api.tudominio.com`, sin `/api`).
3. Push a `main` (o lanza el workflow a mano desde Actions).

### Aviso sobre Safari y github.io

Con el frontend en `github.io` y el backend en otro dominio, la cookie de sesión es de terceros. **Safari bloquea las cookies de terceros**, así que al recargar la página la sesión se pierde y hay que volver a entrar. Para evitarlo, usa un dominio propio para los dos (p. ej. `dashboard.tudominio.com` en Pages y `api.tudominio.com` para el backend): pasan a ser del mismo sitio, puedes dejar `COOKIE_SAMESITE=lax` y define la variable `BASE_PATH=/` en GitHub.

