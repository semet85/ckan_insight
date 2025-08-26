# Build a CKAN 2.9 image with ckanet-insight baked in
FROM ckan/ckan:2.9

# Copy the extension source into the image
COPY ./ckanet-insight /srv/app/src/ckanet-insight

# Install the extension
RUN pip install -e /srv/app/src/ckanet-insight \    && pip cache purge

# (Optional) show installed plugins for debugging during build
RUN python - <<'PY'
import pkg_resources
print('\nInstalled CKAN plugins entry-points:')
for ep in pkg_resources.iter_entry_points('ckan.plugins'):
    print('-', ep.name, '=>', ep.module_name)
PY