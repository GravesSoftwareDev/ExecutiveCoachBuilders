"""
WSGI config for ecb_website project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.insert(0, '/opt/bitnami/apache/htdocs/ecb_website')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecb_website.settings')

application = get_wsgi_application()
