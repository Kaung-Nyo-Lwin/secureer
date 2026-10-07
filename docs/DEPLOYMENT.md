# Running Secureer outside local development

The repository’s default container runs the lightweight reference demo. It is suitable for a small portfolio deployment with persistent SQLite storage and a single application instance.

## Environment

Configure these variables through the hosting provider’s secret/environment settings:

| Variable | Public deployment value |
|---|---|
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | A fresh generated secret |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames without schemes or paths |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | HTTPS origins, such as `https://secureer.example.com` |
| `DJANGO_HTTPS` | `True` when public traffic uses HTTPS |
| `SECUREER_ENGINE` | `demo` for the default container |
| `SECUREER_DATA_DIR` | A writable persistent directory, default `/app/var` in Docker |

Generate the key locally:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Supply that value through the hosting provider. Production startup fails if a key is absent and debug mode is disabled.

If the application is behind a trusted TLS-terminating proxy, set `DJANGO_TRUST_PROXY=True` only when the proxy overwrites `X-Forwarded-Proto`. This allows Django to identify HTTPS requests and apply secure cookies and redirects correctly. `DJANGO_HTTPS=True` enables secure cookies, HTTPS redirects, and HSTS. The health endpoint is exempt from the redirect so a local container probe can use HTTP.

## Container behavior

```bash
docker build -t secureer .
```

At runtime, the image applies migrations and starts Gunicorn on port 8000 as the `app` user. Collected static assets are built into the image and served by WhiteNoise. The image excludes local secrets, databases, notebooks, PDFs, videos, and archived model binaries.

Mount persistent storage at `/app/var`, writable by the container user. A normal Docker named volume inherits the directory’s ownership. When using a host directory, set its ownership for the container’s user rather than making it world-writable.

The Compose file is a local preview: it binds to `127.0.0.1` and supplies a local-only key. A public deployment should use the explicit environment settings above and the hosting provider’s HTTPS routing.

The image provides `/health/` as a lightweight HTTP liveness endpoint. It reports the configured engine without loading models. It does not certify that the ML weights, database schema, or recommendation engine are ready. Confirm startup logs and open the example report after deploying.

## Running without Docker

On Linux, in an activated environment:

```bash
python -m pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn admin.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

Set the public deployment environment before these commands. Configure the hosting platform to proxy requests to port 8000.

## Semantic mode

Install `requirements-ml.txt` in a separate image or Python 3.12 environment, and set `SECUREER_ENGINE=ml`. The standard demo image does not include PyTorch.

Each worker builds and holds its own sentence transformer and fitted pipeline. Start with one worker and a longer request timeout, then size memory and concurrency from measured use. Downloading the initial weights and encoding the CSV rows can exceed a small server’s normal request timeout. Demo mode is useful when quick first interactions matter.

The archived model binaries are not needed. The current application fits its models from the exact bundled rows to avoid the original recommender’s row mismatch. See the [model card](MODEL_CARD.md).

## Personal reports and storage

The public example saves no profile. Personal assessments persist in SQLite until deleted. The report page’s deletion action removes the profile, its report, and skills not referenced elsewhere. Access is limited to the browser session that submitted the assessment; operators still have database access.

For a public portfolio, invite visitors to use nicknames and establish a retention policy. Back up the database if you intend to retain reports, and run Django’s `clearsessions` command periodically to remove expired session records. That command only cleans session records; it does not delete assessment profiles.

For multiple application instances or a larger public service, plan a shared database, automatic report expiry, request throttling, and measured ML capacity before scaling.

## CI and publishing

The application workflow runs Django checks, verifies migration consistency, executes regression tests, and builds/starts the demo image. It does not need ML dependencies or model downloads.

The manual **Publish container** workflow runs the web suite and publishes an image to `ghcr.io/<repository-owner>/<repository-name>` with both `latest` and commit-SHA tags. It uses the repository’s GitHub token and does not depend on the original Docker Hub or DigitalOcean credentials. Publishing an image does not deploy it to a live host.
