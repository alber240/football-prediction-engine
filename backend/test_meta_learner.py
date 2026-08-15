"""
Test Meta-Learner
"""

print("Testing imports...")

try:
    from app.meta_learner.simple_scraper import SimpleScraper
    print("SimpleScraper OK")
except Exception as e:
    print(f"SimpleScraper error: {e}")

try:
    from app.meta_learner.meta_learner import MetaLearner
    print("MetaLearner OK")
except Exception as e:
    print(f"MetaLearner error: {e}")

print("\nTesting MetaLearner...")
try:
    ml = MetaLearner()
    predictions = ml.get_all_predictions('premier-league')
    print(f"Fetched from {len(predictions)} sources")
    for source, preds in predictions.items():
        print(f"  - {source}: {len(preds)} predictions")
except Exception as e:
    print(f"Error: {e}")

print("\nDone!")