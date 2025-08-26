from flask import Blueprint, render_template
import ckan.plugins.toolkit as toolkit

blueprint = Blueprint('ckanet_insight', __name__)

@blueprint.route('/insights/')
def insights_home():
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