"""
Train all XGBoost models
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.xgboost_trainer import XGBoostTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🚀 TRAINING XGBOOST MODELS")
print("   Training on 2020-2024 data for all 6 leagues")
print("=" * 60)

trainer = XGBoostTrainer()
results = trainer.train_all_models()

print("\n" + "=" * 60)
print("✅ TRAINING COMPLETE!")
print("=" * 60)

for league, result in results.items():
    if result['status'] == 'success':
        print(f"   {league}:")
        print(f"      Accuracy: {result['accuracy']:.4f}")
        print(f"      Brier Score: {result['brier_score']:.4f}")
        print(f"      Matches: {result['matches_trained'] + result['matches_tested']}")
    else:
        print(f"   {league}: ❌ {result.get('reason', 'Failed')}")

print("=" * 60)