# ckanet-insight

An extension for CKAN 2.9 that creates and maintains **Insight Groups** from datasets tagged with a special marker tag (default: `insight`). It also adds a landing page at `/insights/` listing these groups so you can easily surface them on your home page.

## How it works

If a dataset has tags: `insight`, `health`, `2024`, it will be added to groups:
- `insight-health`
- `insight-2024`

Datasets without the marker tag are removed from any `insight-*` groups.

---

## Installation (Docker Compose, Development)

1. Mount the extension into your CKAN web container (example path):

```yaml
services:
  ckan-web:
    volumes:
      - ./ckanet-insight:/srv/app/src/ckanet-insight:Z
```

2. Install inside the container:

```bash
docker compose exec ckan-web pip install -e /srv/app/src/ckanet-insight
```

3. Enable the plugin (environment or `production.ini`). Using env vars:

```yaml
environment:
  CKAN__PLUGINS: "envvars image_view text_view recline_view resource_proxy insight"
  CKAN__CKANET__INSIGHT_TAG: "insight"  # optional override
```

4. Restart CKAN:

```bash
docker compose restart ckan-web
```

5. (Optional) Backfill/sync all groups:

```bash
docker compose exec ckan-web ckan -c /etc/ckan/production.ini insight sync-groups
```

6. Visit:

- `/insights/` – landing page listing Insight Groups  
- `/group/insight-<tag>` – each group page

---

## Production build: COPY & install inside the container

Bake the extension into your CKAN image.

### Dockerfile
```dockerfile
# Build a CKAN 2.9 image with ckanet-insight baked in
FROM ckan/ckan:2.9

# Copy the extension source into the image
COPY ./ckanet-insight /srv/app/src/ckanet-insight

# Install the extension
RUN pip install -e /srv/app/src/ckanet-insight \\
    && pip cache purge

# (Optional) show installed plugins for debugging during build
RUN python - <<'PY'
import pkg_resources
print('\nInstalled CKAN plugins entry-points:')
for ep in pkg_resources.iter_entry_points('ckan.plugins'):
    print('-', ep.name, '=>', ep.module_name)
PY
```

### .dockerignore
```gitignore
.git/
__pycache__/
*.pyc
*.pyo
*.egg-info/
.venv/
.idea/
.vscode/
```

### docker-compose.prod.yml
```yaml
version: '3.8'
services:
  ckan-web:
    build:
      context: .
      dockerfile: Dockerfile
    image: my-ckan:2.9-insight
    environment:
      CKAN__PLUGINS: "envvars image_view text_view recline_view resource_proxy insight"
      CKAN__CKANET__INSIGHT_TAG: "insight"
    depends_on:
      - db
      - solr
      - redis
    ports:
      - "5000:5000"

  db:
    image: postgres:12
    environment:
      POSTGRES_DB: ckan
      POSTGRES_USER: ckan
      POSTGRES_PASSWORD: ckan

  solr:
    image: ckan/solr:2.9-solr8

  redis:
    image: redis:6
```

### Build & run
```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Initialize (first time)
```bash
docker compose -f docker-compose.prod.yml exec ckan-web \\
  ckan -c /etc/ckan/production.ini db init
# add sysadmin if needed:
# docker compose -f docker-compose.prod.yml exec ckan-web ckan -c /etc/ckan/production.ini sysadmin add <name> email=<email> password=<pwd>
```

### Backfill Insight Groups
```bash
docker compose -f docker-compose.prod.yml exec ckan-web \\
  ckan -c /etc/ckan/production.ini insight sync-groups
```

---

## Developer Installation

1. Clone repo ini:
```bash
docker compose exec -u root ckan bash
cd src
git clone https://www.github.com/semet85/ckan_insight.git
cd ckan_insight
python setup.py develop
pip install -r dev-requirements.txt
apt update && apt install nano -y
```

2. Install dalam mode *develop* (editable):
```bash
python setup.py develop
# atau
pip install -e .
```

3. Install requirements tambahan untuk development (tests, linters, dll):
```bash
pip install -r dev-requirements.txt
```

4. Jalankan tests (opsional):
```bash
pytest --ckan-ini=test.ini
```

### dev-requirements.txt (contoh)
```
pytest
pytest-cov
ckanapi
black
flake8
```

---

## Configuration

- `ckanet.insight_tag` (string) – marker tag name. Default: `insight`.

Add to `production.ini` as:
```
ckanet.insight_tag = insight
```
or via env var `CKAN__CKANET__INSIGHT_TAG`.

## License

MIT – see `LICENSE`.