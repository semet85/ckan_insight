from math import ceil
from flask import Blueprint, render_template, request, redirect
import ckan.plugins.toolkit as toolkit
from ckan.lib import authz  # ⬅️ tambah ini

blueprint = Blueprint('ckanet_insight', __name__)

def _marker_tag():
    return toolkit.config.get('ckanet.insight_tag', 'insight')

def _current_user():
    # kompatibel ckan 2.9 (flask global)
    return getattr(toolkit.g, 'user', '') or getattr(toolkit.c, 'user', '') or ''

def _require_sysadmin():
    user = _current_user()
    if not user or not authz.is_sysadmin(user):
        toolkit.abort(403, toolkit._('Not authorized to access this page.'))  # 403 untuk non-admin

@blueprint.route('/insights/')
def insights_home():
    ctx = {'ignore_auth': True}
    q = (request.args.get('q') or '').strip().lower()
    order = (request.args.get('order') or 'name_asc').strip()
    page = int(request.args.get('page', 1) or 1)
    per_page = 12

    groups = toolkit.get_action('group_list')(ctx, {'all_fields': True})
    insight_groups = [g for g in groups if (g.get('name') or '').startswith('insight-')]

    results = []
    for g in insight_groups:
        g_full = toolkit.get_action('group_show')(ctx, {'id': g['name'], 'include_datasets': True})
        results.append({
            'name': g_full['name'],
            'title': g_full.get('title') or g_full['name'],
            'description': g_full.get('description') or '',
            'package_count': len(g_full.get('packages') or []),
            'image_url': g_full.get('image_display_url') or g_full.get('image_url') or '',
        })

    # ... (filter, sort, pagination seperti versi kamu saat ini) ...

    is_sysadmin = authz.is_sysadmin(_current_user())
    return render_template(
        'insight/index.html',
        groups=results,  # atau page_items jika kamu pakai pagination
        # total=total, page=page, pages=pages, q=q, order=order, ...
        marker_tag=_marker_tag(),
        is_sysadmin=is_sysadmin,  # ⬅️ kirim ke template
    )

@blueprint.route('/insights/add', methods=['GET', 'POST'])
def insights_add():
    _require_sysadmin()  # ⬅️ wajib admin

    marker = _marker_tag()
    if request.method == 'POST':
        dataset_ref = (request.form.get('dataset') or '').strip()
        topics_raw = (request.form.get('topics') or '')
        topics = [t.strip() for t in topics_raw.replace(';', ',').split(',') if t.strip()]

        if not dataset_ref:
            toolkit.h.flash_error('Nama/ID dataset wajib diisi.')
            return render_template('insight/add.html', dataset=dataset_ref, topics=topics_raw, marker_tag=marker)

        ctx = {'user': _current_user()}
        try:
            pkg = toolkit.get_action('package_show')(ctx, {'id': dataset_ref})
        except toolkit.ObjectNotFound:
            toolkit.h.flash_error('Dataset tidak ditemukan.')
            return render_template('insight/add.html', dataset=dataset_ref, topics=topics_raw, marker_tag=marker)

        existing = [t.get('name') for t in (pkg.get('tags') or []) if t.get('name')]
        wanted = set(existing); wanted.add(marker); [wanted.add(t) for t in topics]
        new_tags = [{'name': name} for name in sorted(wanted)]

        try:
            toolkit.get_action('package_update')(ctx, {'id': pkg['id'], 'tags': new_tags})
            toolkit.h.flash_success('Dataset berhasil ditandai sebagai Insight.')
            return redirect(toolkit.h.url_for('dataset.read', id=pkg['name']))
        except toolkit.NotAuthorized:
            toolkit.h.flash_error('Anda tidak punya izin untuk mengubah dataset ini.')
        except toolkit.ValidationError as e:
            toolkit.h.flash_error('Gagal memperbarui tag: %s' % getattr(e, 'error_dict', e))
        except Exception as e:
            toolkit.h.flash_error('Terjadi kesalahan: %s' % e)

        return render_template('insight/add.html', dataset=dataset_ref, topics=topics_raw, marker_tag=marker)

    return render_template('insight/add.html', marker_tag=marker)
