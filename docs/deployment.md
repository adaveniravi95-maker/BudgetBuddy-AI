# Production Deployment

The deployment target is Render: a Django web service, a private managed PostgreSQL database, and a static React site. Render supplies HTTPS certificates and redirects static-site HTTP traffic to HTTPS. The API trusts Render's forwarded HTTPS protocol header and redirects production HTTP requests to HTTPS.

## Services

`render.yaml` defines both services, PostgreSQL, generated Django and JWT signing secrets, the API health check, static-site SPA routing, and migration execution before API deploys. The initial service plans are paid, small production plans; Render billing applies. Free PostgreSQL is intentionally not selected because Render expires free databases after 30 days.

The frontend's production `VITE_API_URL` is set to the API service origin. If service names or custom domains change, update `VITE_API_URL`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` in the Blueprint and redeploy. Django uses Render's `RENDER_EXTERNAL_HOSTNAME` for `ALLOWED_HOSTS` unless you explicitly set `ALLOWED_HOSTS` yourself.

The deploy migration hook creates/updates the schema; it does not copy existing records from the local SQLite database. Export/import any local records only if they are explicitly meant to become production data, and verify ownership before importing.

## Deploy

1. Push the project, including `render.yaml`, to a GitHub, GitLab, or Bitbucket repository accessible to Render.
2. In Render, create a Blueprint instance from that repository and review the paid service/database plans and resulting monthly cost before applying it.
3. Wait for PostgreSQL creation, API build, `collectstatic`, pre-deploy migrations, and frontend build to finish.
4. Confirm `https://budgetbuddy-api.onrender.com/api/health/` returns `{"status":"ok"}` and the frontend URL serves the login screen over HTTPS.
5. Test registration/login, protected resource APIs, analytics, report exports, and cross-user isolation using dedicated non-production test accounts. Do not use real financial data for deployment smoke tests.
6. Configure a production SMTP provider in the API service environment (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`) only if email delivery is enabled.

The repository does not contain provider credentials, a connected Render account, a Git remote, a production custom domain, or production test accounts. Therefore the Blueprint and production settings are prepared here, but provisioning services, applying migrations to a live database, and the live end-to-end/isolation tests must be completed in the Render account before this can be called deployed.

## Connect an existing Render Django service

If the Django web service already exists, keep it and create PostgreSQL separately in the same Render region. In the database's **Connect** page, copy its **Internal Database URL** into the existing Django service's environment as `DATABASE_URL`. Do not use the external URL for a service in the same Render region, and do not commit the URL to the repository.

Set or verify these environment variables on the Django service:

| Key | Value |
| --- | --- |
| `DJANGO_DEBUG` | `false` |
| `SECRET_KEY` | A generated, private secret |
| `DATABASE_URL` | The PostgreSQL **Internal Database URL** |
| `ALLOWED_HOSTS` | Optional; if set, include the service hostname, e.g. `budgetbuddy-ai-hhob.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Your frontend's exact HTTPS origin, with no trailing slash |
| `CSRF_TRUSTED_ORIGINS` | Your frontend's exact HTTPS origin, with no trailing slash |
| `SECURE_SSL_REDIRECT` | `true` |

When `ALLOWED_HOSTS` is not set, Django uses Render's `RENDER_EXTERNAL_HOSTNAME`. If you set it explicitly, it must match the existing service hostname; an unrelated hostname causes Django to reject requests with `DisallowedHost`.

Use the repository root as the service's **Root Directory**, with these commands:

```text
Build:  pip install -r requirements.txt && python manage.py collectstatic --no-input
Start:  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Set the service's **Pre-Deploy Command** to `python manage.py migrate --noinput` if available. Otherwise, run that command once in the service's Render Shell after `DATABASE_URL` is configured and before testing the API.

For a separate Render static frontend, set `VITE_API_URL` to `https://budgetbuddy-ai-hhob.onrender.com/api` (or your actual API origin followed by `/api`) and redeploy the frontend, since Vite embeds this value at build time. Ensure `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` on Django match the frontend's actual HTTPS origin.

After saving the environment variables, redeploy the Django service and verify `https://budgetbuddy-ai-hhob.onrender.com/api/health/` returns `{"status":"ok"}`. If deployment still fails, inspect the first traceback or error in the Render **Deploy Logs**; the health check cannot pass until the database connection and migrations succeed.