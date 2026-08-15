print("Testing imports...")

try:
    from app.websocket.live_updates import ConnectionManager
    print("✅ WebSocket OK")
except Exception as e:
    print(f"❌ WebSocket: {e}")

try:
    from app.services.live_matches import LiveMatchService
    print("✅ LiveMatch OK")
except Exception as e:
    print(f"❌ LiveMatch: {e}")

try:
    from app.scheduler.etl_scheduler import start_scheduler
    print("✅ Scheduler OK")
except Exception as e:
    print(f"❌ Scheduler: {e}")

print("\nDone!")