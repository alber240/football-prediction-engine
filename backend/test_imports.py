"""
Test all imports
"""

print("Testing imports...")

try:
    from app.websocket.live_updates import ConnectionManager
    print("✅ WebSocket OK")
except Exception as e:
    print(f"❌ WebSocket error: {e}")

try:
    from app.services.live_matches import LiveMatchService
    print("✅ LiveMatch OK")
except Exception as e:
    print(f"❌ LiveMatch error: {e}")

try:
    from app.scheduler.etl_scheduler import start_scheduler
    print("✅ Scheduler OK")
except Exception as e:
    print(f"❌ Scheduler error: {e}")

print("\nAll imports tested!")