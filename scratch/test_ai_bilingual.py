import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import Task, AISuggestion
from app.ai_engine import analyze_and_optimize_tasks

def test_bilingual_fallback():
    app = create_app()
    with app.app_context():
        print("[TEST] Running isolated context test for AI Daily...")
        
        # Mocking some tasks in memory or fetching existing tasks
        # Let's create dummy tasks using a mock class to test offline fallback
        class MockTask:
            def __init__(self, id, title, description, period, priority, start_time, end_time, is_completed):
                self.id = id
                self.title = title
                self.description = description
                self.period = period
                self.priority = priority
                self.start_time = start_time
                self.end_time = end_time
                self.is_completed = is_completed

        tasks = [
            MockTask(1, "Toplantı", "Haftalık koordinasyon toplantısı", "daily", "High", "09:00", "10:30", False),
            MockTask(2, "Egzersiz", "Günlük spor rutini", "daily", "Low", "08:00", "09:00", True),
            MockTask(3, "Kod Gözden Geçirme", "Proje kod analizi", "daily", "Medium", "10:00", "11:30", False)
        ]

        print("[TEST] Tasks created. Analyzing...")
        result = analyze_and_optimize_tasks(tasks)
        
        assert isinstance(result, dict), "Result must be a dictionary!"
        assert "ai_evaluation_tr" in result, "Result must contain Turkish analysis!"
        assert "ai_evaluation_en" in result, "Result must contain English analysis!"
        assert "tasks_priority_order" in result, "Result must contain task priority order!"
        
        print("\n--- TURKISH EVALUATION ---")
        print(result["ai_evaluation_tr"][:200].encode('ascii', 'ignore').decode('ascii') + "...")
        print("\n--- ENGLISH EVALUATION ---")
        print(result["ai_evaluation_en"][:200].encode('ascii', 'ignore').decode('ascii') + "...")
        print("\n--- PRIORITY ORDER ---")
        print(result["tasks_priority_order"])
        
        print("\n[TEST SUCCESS] Fallback engine works flawlessly!")

if __name__ == "__main__":
    test_bilingual_fallback()
