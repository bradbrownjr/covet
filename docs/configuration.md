# Configuration reference

All settings are loaded from environment variables (prefix `COVET_`) with
overrides from `${COVET_CONFIG_DIR}/covet.env` and `covet.yaml`. Secrets
support a `<NAME>_FILE` convention for Docker secrets and Unraid file
mounts.

## Core / runtime

| Variable               | Default       | Notes                                   |
| ---------------------- | ------------- | --------------------------------------- |
| `COVET_DATA_DIR`       | `/data`       | Photos, SQLite db, uploads              |
| `COVET_CONFIG_DIR`     | `/config`     | Optional config files, secret.key       |
| `COVET_HOST`           | `0.0.0.0`     |                                         |
| `COVET_PORT`           | `8000`        |                                         |
| `COVET_LOG_LEVEL`      | `INFO`        | `DEBUG`, `INFO`, `WARNING`, `ERROR`     |
| `COVET_LOG_FORMAT`     | `console`     | `console` or `json`                      |
| `COVET_TZ`             | `UTC`         | IANA timezone name                       |
| `PUID` / `PGID`        | `1000`/`1000` | Container user (Unraid image: `99/100`) |
| `UMASK`                | `0022`        |                                         |

## Database

Provide a single SQLAlchemy URL **or** discrete fields:

```env
COVET_DATABASE_URL=postgresql+psycopg://covet:secret@db:5432/covet
```

| Variable                       | Default | Notes                                                     |
| ------------------------------ | ------- | --------------------------------------------------------- |
| `COVET_DATABASE_URL`           | —       | Full SQLAlchemy URL; overrides discrete fields           |
| `COVET_DB_TYPE`                | `sqlite`| `sqlite`, `postgresql`, `mysql`, `mariadb`                |
| `COVET_DB_HOST`                | —       |                                                           |
| `COVET_DB_PORT`                | —       | Auto-defaults per type                                    |
| `COVET_DB_NAME`                | `covet` | Database name (Covet manages tables itself)               |
| `COVET_DB_USER`                | —       |                                                           |
| `COVET_DB_PASSWORD`            | —       | Use `COVET_DB_PASSWORD_FILE` for Docker secrets           |
| `COVET_DB_SSLMODE`             | —       | Passthrough where supported                                |
| `COVET_DB_POOL_SIZE`           | `5`     |                                                           |
| `COVET_DB_POOL_MAX_OVERFLOW`   | `10`    |                                                           |
| `COVET_DB_AUTO_MIGRATE`        | `true`  | Run Alembic on startup                                    |

## Reverse proxy / public URL

| Variable                  | Default                              | Notes                                       |
| ------------------------- | ------------------------------------ | ------------------------------------------- |
| `COVET_PUBLIC_URL`        | `http://localhost:8000`              | Used for OIDC redirects, share links, CORS  |
| `COVET_BEHIND_PROXY`      | `false`                              | Trust `X-Forwarded-*` headers               |
| `COVET_TRUSTED_PROXIES`   | RFC1918 ranges                       | Comma-separated CIDRs                       |
| `COVET_FORCE_HTTPS`       | auto (true if PUBLIC_URL is https)   |                                             |
| `COVET_CORS_ORIGINS`      | `${PUBLIC_URL}`                      | Comma-separated                             |
| `COVET_ALLOWED_HOSTS`     | derived from PUBLIC_URL host         | Comma-separated host header allowlist        |

### Caddy example

```caddyfile
covet.example.com {
    reverse_proxy covet:8000
}
```

Pair with:

```env
COVET_PUBLIC_URL=https://covet.example.com
COVET_BEHIND_PROXY=true
COVET_ALLOWED_HOSTS=covet.example.com
```

## Sessions / auth

| Variable                          | Default         | Notes                                          |
| --------------------------------- | --------------- | ---------------------------------------------- |
| `COVET_SECRET_KEY`                | auto-generated  | Persisted to `${CONFIG_DIR}/secret.key` if unset |
| `COVET_SESSION_COOKIE_NAME`       | `covet_session` |                                                |
| `COVET_SESSION_COOKIE_SECURE`     | auto            | Defaults from `FORCE_HTTPS`                    |
| `COVET_SESSION_COOKIE_SAMESITE`   | `lax`           |                                                |
| `COVET_SESSION_TTL_HOURS`         | `720`           |                                                |
| `COVET_REGISTRATION_ENABLED`      | `false`         | First-run wizard always allowed                |
| `COVET_PASSWORD_MIN_LENGTH`       | `12`            |                                                |

## OIDC / OAuth (optional)

Master toggles:

| Variable                          | Default   |
| --------------------------------- | --------- |
| `COVET_OIDC_ENABLED`              | `false`   |
| `COVET_OIDC_AUTO_CREATE_USERS`    | `true`    |
| `COVET_OIDC_DEFAULT_ROLE`         | `viewer`  |

Per-provider (replace `<NAME>`, e.g. `AUTHENTIK`, `GOOGLE`):

| Variable                                   | Default                                               |
| ------------------------------------------ | ----------------------------------------------------- |
| `COVET_OIDC_<NAME>_DISPLAY_NAME`           | `<NAME>`                                              |
| `COVET_OIDC_<NAME>_ISSUER`                 | required                                              |
| `COVET_OIDC_<NAME>_CLIENT_ID`              | required                                              |
| `COVET_OIDC_<NAME>_CLIENT_SECRET`          | required (or `_FILE`)                                 |
| `COVET_OIDC_<NAME>_SCOPES`                 | `openid profile email`                                |
| `COVET_OIDC_<NAME>_REDIRECT_URI`           | `${PUBLIC_URL}/auth/oidc/<name>/callback`             |
| `COVET_OIDC_<NAME>_ADMIN_GROUPS`           | comma-separated group claims auto-granted admin       |
| `COVET_OIDC_<NAME>_USERNAME_CLAIM`         | `preferred_username`                                  |

## Photo storage

| Variable                          | Default                  |
| --------------------------------- | ------------------------ |
| `COVET_PHOTOS_DIR`                | `${DATA_DIR}/photos`     |
| `COVET_PHOTOS_MAX_BYTES`          | `26214400` (25 MiB)      |
| `COVET_PHOTOS_THUMBNAIL_SIZES`    | `256,1024`               |

## Sync

| Variable                          | Default |
| --------------------------------- | ------- |
| `COVET_SYNC_SNAPSHOT_INTERVAL`    | `100`   |
| `COVET_SYNC_RETENTION_DAYS`       | `30`    |
| `COVET_SYNC_MAX_BATCH`            | `500`   |

## Rate limiting

| Variable                   | Default       |
| -------------------------- | ------------- |
| `COVET_RATE_LIMIT_LOGIN`   | `5/minute`    |
| `COVET_RATE_LIMIT_API`     | `120/minute`  |
| `COVET_API_TOKEN_TTL_DAYS` | `0` (never)   |

## SMTP (optional, future use)

| Variable               | Default | Notes                          |
| ---------------------- | ------- | ------------------------------ |
| `COVET_SMTP_HOST`      | —       |                                |
| `COVET_SMTP_PORT`      | `587`   |                                |
| `COVET_SMTP_USER`      | —       |                                |
| `COVET_SMTP_PASSWORD`  | —       | Use `_FILE` for Docker secrets |
| `COVET_SMTP_FROM`      | —       |                                |
| `COVET_SMTP_STARTTLS`  | `true`  |                                |

## First-run admin bootstrap

If both are set on first launch, an admin is created and the in-UI first-run
wizard is skipped:

| Variable                | Notes                          |
| ----------------------- | ------------------------------ |
| `COVET_ADMIN_USERNAME`  |                                |
| `COVET_ADMIN_PASSWORD`  | Use `_FILE` for Docker secrets |
| `COVET_ADMIN_EMAIL`     | Optional                       |

## Integration API keys

These can also be set in the admin UI; environment values take precedence.

| Variable                            | Notes                                        |
| ----------------------------------- | -------------------------------------------- |
| `COVET_DISCOGS_TOKEN`               | Personal access token                        |
| `COVET_TMDB_API_KEY`                |                                              |
| `COVET_IGDB_CLIENT_ID`              |                                              |
| `COVET_IGDB_CLIENT_SECRET`          | Use `_FILE` for Docker secrets               |
| `COVET_MUSICBRAINZ_USER_AGENT`      | Default `Covet/1.0 (+${PUBLIC_URL})`         |
| `COVET_UPCITEMDB_KEY`               | Optional fallback for unknown barcodes       |
