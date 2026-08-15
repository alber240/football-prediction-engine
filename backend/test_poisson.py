"""
Test the Poisson Model
"""

from app.poisson_model import PoissonModel
from app.models import get_db, League, Team, Match
import numpy as np

print("=" * 60)
print("TESTING POISSON MODEL")
print("=" * 60)

# Initialize model
model = PoissonModel()
db = next(get_db())

# Get a league (Premier League)
premier_league = db.query(League).filter_by(name="Premier League").first()
print(f"\n📌 League: {premier_league.name}")

# Calculate league averages
print("\n📊 League Averages:")
avg = model.calculate_league_averages(premier_league.id)
print(f"   Avg Home Goals: {avg['avg_home_goals']:.3f}")
print(f"   Avg Away Goals: {avg['avg_away_goals']:.3f}")
print(f"   Avg Total Goals: {avg['avg_total_goals']:.3f}")
print(f"   Matches: {avg['matches']}")

# Calculate team strengths
print("\n📊 Team Strengths (Top 5 teams by attack):")
strengths = model.calculate_team_strengths(premier_league.id)

# Sort teams by home attack
sorted_teams = sorted(
    [(team_id, data) for team_id, data in strengths.items()],
    key=lambda x: x[1].get('home_attack', 0),
    reverse=True
)

for team_id, data in sorted_teams[:5]:
    team = db.query(Team).filter_by(id=team_id).first()
    print(f"\n   {team.name}:")
    print(f"      Home Attack: {data.get('home_attack', 1.0):.3f}")
    print(f"      Home Defense: {data.get('home_defense', 1.0):.3f}")
    print(f"      Away Attack: {data.get('away_attack', 1.0):.3f}")
    print(f"      Away Defense: {data.get('away_defense', 1.0):.3f}")

# Test predictions for a match
print("\n" + "=" * 60)
print("MATCH PREDICTION")

# Get a sample match (Manchester City vs Arsenal)
man_city = db.query(Team).filter_by(name="Manchester City").first()
arsenal = db.query(Team).filter_by(name="Arsenal").first()

if man_city and arsenal:
    print(f"\n🏟️  Match: {man_city.name} vs {arsenal.name}")
    print(f"   League: {premier_league.name}")
    
    # Predict with Poisson model
    prediction = model.predict_match(
        home_team_id=man_city.id,
        away_team_id=arsenal.id,
        league_id=premier_league.id
    )
    
    print(f"\n📊 Expected Goals:")
    print(f"   {man_city.name}: {prediction['expected_home_goals']:.3f}")
    print(f"   {arsenal.name}: {prediction['expected_away_goals']:.3f}")
    
    print(f"\n🎯 1X2 Probabilities:")
    print(f"   {man_city.name} Win: {prediction['home_win']*100:.1f}%")
    print(f"   Draw: {prediction['draw']*100:.1f}%")
    print(f"   {arsenal.name} Win: {prediction['away_win']*100:.1f}%")
    
    print(f"\n⚽ Over/Under 2.5:")
    print(f"   Over 2.5: {prediction['over_25']*100:.1f}%")
    print(f"   Under 2.5: {prediction['under_25']*100:.1f}%")
    
    print(f"\n📋 Most Likely Scores:")
    for score, prob in prediction['most_likely_scores']:
        print(f"   {score}: {prob*100:.1f}%")
    
    print(f"\n💪 Confidence Score: {prediction['confidence_score']*100:.1f}%")

# Optimize Dixon-Coles tau
print("\n" + "=" * 60)
print("OPTIMIZING DIXON-COLES TAU")
print("Optimizing... (this may take a few seconds)")
tau = model.optimize_dixon_coles_tau(premier_league.id)
print(f"✅ Optimized τ: {tau:.4f}")

# Close connections
model.close()
db.close()

print("\n" + "=" * 60)
print("✅ POISSON MODEL TEST COMPLETE!")
print("=" * 60)