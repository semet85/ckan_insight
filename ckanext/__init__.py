# -*- coding: utf-8 -*-
# Declare "ckanext" as a namespace package for CKAN extensions.
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except Exception:
    pass
