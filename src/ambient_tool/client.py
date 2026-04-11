import requests

from ambient_tool.config import API_KEY, APPLICATION_KEY

BASE_URL = "https://api.ambientweather.net/v1"


class AmbientWeatherClient:
    def __init__(self, api_key, application_key):
        if not api_key or not application_key:
            raise ValueError("Missing Ambient Weather API credentials.")
        self.api_key = api_key
        self.application_key = application_key

    def get_devices(self):
        response = requests.get(
            f"{BASE_URL}/devices",
            params={
                "apiKey": self.api_key,
                "applicationKey": self.application_key,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


def build_client():
    return AmbientWeatherClient(API_KEY, APPLICATION_KEY)
