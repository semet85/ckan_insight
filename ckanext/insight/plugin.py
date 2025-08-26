import logging
import click
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from .blueprints import insight as insight_bp
from .lib.insight_groups import (
    sync_insight_groups_for_package,
    rebuild_all_insight_groups,
)

log = logging.getLogger(__name__)


def _get_insight_tag_from_config():
    cfg = toolkit.config
    return cfg.get('ckanet.insight_tag', 'insight')


class InsightPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IClick)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'insight')

    # IBlueprint
    def get_blueprint(self):
        return [insight_bp.blueprint]

    # IPackageController
    def after_create(self, context, pkg_dict):
        try:
            sync_insight_groups_for_package(pkg_dict, _get_insight_tag_from_config())
        except Exception:
            log.exception('ckanet-insight: after_create sync failed')

    def after_update(self, context, pkg_dict):
        try:
            sync_insight_groups_for_package(pkg_dict, _get_insight_tag_from_config())
        except Exception:
            log.exception('ckanet-insight: after_update sync failed')

    # IClick
    def get_commands(self):
        @click.group()
        def insight():
            """Insight utilities"""
            pass

        @insight.command('sync-groups')
        @click.option('--tag', 'insight_tag', default=None,
                      help='Marker tag for insight datasets (default: "insight")')
        def sync_groups_cmd(insight_tag):
            if not insight_tag:
                insight_tag = _get_insight_tag_from_config()
            click.echo(f'Rebuilding insight groups with marker tag "{insight_tag}"...')
            stats = rebuild_all_insight_groups(insight_tag)
            click.echo(f"Done: created_groups={stats['created_groups']}, "
                       f"updated_links={stats['updated_links']}, removed_links={stats['removed_links']}")

        return [insight]