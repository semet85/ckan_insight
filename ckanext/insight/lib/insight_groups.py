import re
import unicodedata
import ckan.plugins.toolkit as toolkit

INSIGHT_GROUP_PREFIX = 'insight-'


def _slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^a-zA-Z0-9]+', '-', value).strip('-').lower()
    return value or 'untitled'


def _site_context():
    site_user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    return {'user': site_user['name']}


def _ensure_group(tag_display):
    ctx = _site_context()
    name = INSIGHT_GROUP_PREFIX + _slugify(tag_display)
    title = f'Insight: {tag_display}'

    try:
        grp = toolkit.get_action('group_show')(ctx, {'id': name})
        if grp.get('title') != title:
            toolkit.get_action('group_patch')(ctx, {'id': name, 'title': title})
        return name
    except toolkit.ObjectNotFound:
        pass

    toolkit.get_action('group_create')(ctx, {
        'name': name,
        'title': title,
        'description': f'Datasets tagged as insights for "{tag_display}".',
        'users': [],
    })
    return name


def _current_insight_groups_for_package(pkg_dict):
    groups = pkg_dict.get('groups') or []
    return set([g.get('name') for g in groups if (g.get('name') or '').startswith(INSIGHT_GROUP_PREFIX)])


def _add_pkg_to_group(group_name, package_id):
    ctx = _site_context()
    try:
        toolkit.get_action('member_create')(ctx, {
            'id': group_name,
            'object': package_id,
            'object_type': 'package',
            'capacity': 'public'
        })
    except toolkit.ValidationError:
        pass


def _remove_pkg_from_group(group_name, package_id):
    ctx = _site_context()
    try:
        toolkit.get_action('member_delete')(ctx, {
            'id': group_name,
            'object': package_id,
            'object_type': 'package',
        })
    except toolkit.ObjectNotFound:
        pass


def sync_insight_groups_for_package(pkg_dict, insight_tag='insight'):
    if not pkg_dict or not pkg_dict.get('id'):
        return

    tags = [t.get('name') or t.get('display_name') for t in (pkg_dict.get('tags') or [])]
    tags = [t for t in tags if t]
    tags_lower = set([t.lower() for t in tags])

    if insight_tag.lower() not in tags_lower:
        for g in _current_insight_groups_for_package(pkg_dict):
            _remove_pkg_from_group(g, pkg_dict['id'])
        return

    effective_tags = [t for t in tags if t.lower() != insight_tag.lower()]

    wanted_groups = set()
    for t in effective_tags:
        gname = _ensure_group(t)
        wanted_groups.add(gname)
        _add_pkg_to_group(gname, pkg_dict['id'])

    current = _current_insight_groups_for_package(pkg_dict)
    for g in (current - wanted_groups):
        _remove_pkg_from_group(g, pkg_dict['id'])


def rebuild_all_insight_groups(insight_tag='insight'):
    ctx = _site_context()
    rows = 100
    start = 0
    created_groups = 0
    updated_links = 0
    removed_links = 0

    while True:
        q = f'tags:{insight_tag}'
        res = toolkit.get_action('package_search')(ctx, {'q': q, 'rows': rows, 'start': start})
        for pkg in res.get('results', []):
            before = _current_insight_groups_for_package(pkg)
            sync_insight_groups_for_package(pkg, insight_tag)
            after = _current_insight_groups_for_package(pkg)
            updated_links += len(after - before)
        start += rows
        if start >= (res.get('count') or 0):
            break

    start = 0
    while True:
        res = toolkit.get_action('package_search')(ctx, {'q': f'-tags:{insight_tag}', 'rows': rows, 'start': start})
        for pkg in res.get('results', []):
            for g in _current_insight_groups_for_package(pkg):
                _remove_pkg_from_group(g, pkg['id'])
                removed_links += 1
        start += rows
        if start >= (res.get('count') or 0):
            break

    return {
        'created_groups': created_groups,
        'updated_links': updated_links,
        'removed_links': removed_links,
    }