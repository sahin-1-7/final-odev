import os
import sys

# Add the workspace directory to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import User

def test_language_rendering():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Configure stdout to handle non-ascii characters safely
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Pre-create test user under a temporary app context
    with app.app_context():
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
        test_user_id = test_user.id
        
    # Languages to test and their expected welcome & chip strings
    lang_assertions = {
        'tr': {
            'welcome': 'Merhaba',
            'chip_conflict': 'Çakışmaları Bul',
            'chip_sort': 'Görevleri Sırala',
            'alert_clean': 'Sohbet geçmişinizi tamamen temizlemek istediğinize emin misiniz?'
        },
        'en': {
            'welcome': 'Hello',
            'chip_conflict': 'Find Conflicts',
            'chip_sort': 'Sort Tasks',
            'alert_clean': 'Are you sure you want to completely clear your chat history?'
        },
        'fr': {
            'welcome': 'Bonjour',
            'chip_conflict': 'Trouver des Conflits',
            'chip_sort': 'Trier les Tâches',
            'alert_clean': 'Êtes-vous sûr de vouloir effacer complètement votre historique de discussion ?'
        },
        'es': {
            'welcome': '¡Hola',
            'chip_conflict': 'Buscar Conflictos',
            'chip_sort': 'Ordenar Tareas',
            'alert_clean': '¿Estás seguro de que deseas limpiar completamente tu historial de chat?'
        },
        'hi': {
            'welcome': 'नमस्ते',
            'chip_conflict': 'संघर्ष खोजें',
            'chip_sort': 'कार्यों को क्रमबद्ध करें',
            'alert_clean': 'क्या आप वाकई अपना चैट इतिहास पूरी तरह से साफ़ करना चाहते हैं?'
        },
        'ar': {
            'welcome': 'مرحباً',
            'chip_conflict': 'العثور على التعارضات',
            'chip_sort': 'ترتيب المهام',
            'alert_clean': 'هل أنت متأكد أنك تريد مسح سجل المحادثة بالكامل؟'
        }
    }
    
    success = True
    for lang, expected in lang_assertions.items():
        print(f"\n--- Testing language: {lang.upper()} ---")
        
        # Open a fresh app context for each test case to clean Babel cache
        with app.app_context():
            with app.test_client() as client:
                # Log in the user using the test client session
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(test_user_id)
                    sess['_fresh'] = True
                
                # Request the AI Chat page with lang query parameter
                response = client.get(f'/tasks/ai/chat?lang={lang}')
                assert response.status_code == 200, f"Failed to load AI Chat page in {lang}"
                
                html = response.data.decode('utf-8')
                
                # Verify welcome message
                if expected['welcome'] in html:
                    print(f"  [PASS] Welcome message found")
                else:
                    print(f"  [FAIL] Welcome message NOT found: '{expected['welcome']}'")
                    success = False
                
                # Verify suggestion chips
                if expected['chip_conflict'] in html:
                    print(f"  [PASS] Chip (conflict) found")
                else:
                    print(f"  [FAIL] Chip (conflict) NOT found: '{expected['chip_conflict']}'")
                    success = False
                    
                if expected['chip_sort'] in html:
                    print(f"  [PASS] Chip (sort) found")
                else:
                    print(f"  [FAIL] Chip (sort) NOT found: '{expected['chip_sort']}'")
                    success = False
                
                # Verify Javascript clean chat confirmation message
                if expected['alert_clean'] in html:
                    print(f"  [PASS] Confirm alert found")
                else:
                    print(f"  [FAIL] Confirm alert NOT found: '{expected['alert_clean']}'")
                    success = False
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Language switching for AI assistant is 100% correct.")
    else:
        print("\n❌ SOME TESTS FAILED! Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    test_language_rendering()
