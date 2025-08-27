from flask import Blueprint, render_template, request, redirect
import ckan.plugins.toolkit as toolkit

blueprint = Blueprint('ckanet_insight', __name__)

def _marker_tag():
    # Ambil dari config, default 'insight'
    return toolkit.config.get('ckanet.insight_tag', 'insight')

@blueprint.route('/insights/')
def insights_home():
    """List all Insight Groups with dataset counts."""
    ctx = {'ignore_auth': True}
    groups = toolkit.get_action('group_list')(ctx, {'all_fields': True})
    insight_groups = [g for g in groups if (g.get('name') or '').startswith('insight-')]

    results = []
    for g in insight_groups:
        g_full = toolkit.get_action('group_show')(ctx, {'id': g['name'], 'include_datasets': True})
        results.append({
            'name': g_full['name'],
            'title': g_full.get('title') or g_full['name'],
            'package_count': len(g_full.get('packages') or []),
        })

    results.sort(key=lambda x: (-x['package_count'], x['title'].lower()))
    return render_template('insight/index.html', groups=results)

@blueprint.route('/insights/add', methods=['GET', 'POST'])
def insights_add():
    """
    Form sederhana untuk menandai sebuah dataset sebagai Insight:
      - menambahkan tag penanda (default: 'insight')
      - menambahkan tag topik dari input user (koma-separated)
    """
    marker = _marker_tag()

    if request.method == 'POST':
        dataset_ref = (request.form.get('dataset') or '').strip()
        topics_raw = (request.form.get('topics') or '')
        topics = [t.strip() for t in topics_raw.replace(';', ',').split(',') if t.strip()]

        if not dataset_ref:
            toolkit.h.flash_error('Nama/ID dataset wajib diisi.')
            return render_template('insight/add.html', dataset=dataset_ref, topics=topics_raw, marker_tag=marker)

        # Aksi di bawah berjalan atas nama user yang login
        user = getattr(toolkit.g, 'user', '') or getattr(toolkit.c, 'user', '') or ''
        ctx = {'user': user}

        try:
            pkg = toolkit.get_action('package_show')(ctx, {'id': dataset_ref})
        except toolkit.ObjectNotFound:
            toolkit.h.flash_error('Dataset tidak ditemukan.')
            return render_template('insight/add.html', dataset=dataset_ref, topics=topics_raw, marker_tag=marker)

        # Komposisi ulang daftar tag
        existing = [t.get('name') for t in (pkg.get('tags') or []) if t.get('name')]
        wanted = set(existing)
        wanted.add(marker)
        for t in topics:
            wanted.add(t)

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

        # Jika ada error, render ulang form dengan nilai sebelumnya
        return render_template('insight/add.html', dataset=dataset_ref, topics=topics_raw, marker_tag=marker)

    # GET
    return render_template('insight/add.html', marker_tag=marker)
