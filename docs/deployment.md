# Production Deployment

The deployment target is Render: a Django web service, a private managed PostgreSQL database, and a static React site. Render supplies HTTPS certificates and redirects static-site HTTP traffic to HTTPS. The API trusts Render's forwarded HTTPS protocol header and redirects production HTTP requests to HTTPS.

## Services

`render.yaml` defines both services, PostgreSQL, generated Django and JWT signing secrets, the API health check, static-site SPA routing, and migration execution before API deploys. The initial service plans are paid, small production plans; Render billing applies. Free PostgreSQL is intentionally not selected because Render expires free databases after 30 days.

The frontend's production `VITE_API_URL` is set to the API service origin. If service names or custom domains change, update `VITE_API_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` in the Blueprint and redeploy.

The deploy migration hook creates/updates the schema; it does not copy existing records from the local SQLite database. Export/import any local records only if they are explicitly meant to become production data, and verify ownership before importing.

## Deploy

1. Push the project, including `render.yaml`, to a GitHub, GitLab, or Bitbucket repository accessible to Render.
2. In Render, create a Blueprint instance from that repository and review the paid service/database plans and resulting monthly cost before applying it.
3. Wait for PostgreSQL creation, API build, `collectstatic`, pre-deploy migrations, and frontend build to finish.
4. Confirm `https://budgetbuddy-api.onrender.com/api/health/` returns `{"status":"ok"}` and the frontend URL serves the login screen over HTTPS.
5. Test registration/login, protected resource APIs, analytics, report exports, and cross-user isolation using dedicated non-production test accounts. Do not use real financial data for deployment smoke tests.
6. Configure a production SMTP provider in the API service environment (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`) only if email delivery is enabled.

The repository does not contain provider credentials, a connected Render account, a Git remote, a production custom domain, or production test accounts. Therefore the Blueprint and production settings are prepared here, but provisioning services, applying migrations to a live database, and the live end-to-end/isolation tests must be completed in the Render account before this can be called deployed.