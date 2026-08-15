from app.services.api_football import APIFootballService
print("Import successful!")
service = APIFootballService()
print("Service created!")
print("Leagues:", service.fetch_leagues())
