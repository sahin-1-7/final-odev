import os
import sys

# Add workspace directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from flask_babel import get_locale as babel_get_locale, refresh, gettext as _
from app import get_locale as app_get_locale

app = create_app()
with app.app_context():
    for lang in ['tr', 'en', 'fr', 'es']:
        with app.test_request_context(f'/tasks/ai/chat?lang={lang}'):
            # Force refresh to make sure locale is re-evaluated
            refresh()
            print(f"Request with lang={lang}:")
            print("  app_get_locale():", app_get_locale())
            print("  babel_get_locale():", babel_get_locale())
            print("  Translation of 'AI Asistanı':", _('AI Asistanı'))
            print("  Translation of 'Çakışmaları Bul':", _('Çakışmaları Bul'))
