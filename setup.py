from setuptools import setup, find_packages

setup(
    name='ckanet-insight',
    version='0.1.0',
    description='Insight Groups extension for CKAN 2.9',
    packages=find_packages(),
    namespace_packages=['ckanext'],
    include_package_data=True,
    install_requires=[],
    entry_points='''
        [ckan.plugins]
        insight=ckanext.insight.plugin:InsightPlugin
    ''',
    zip_safe=False,
)