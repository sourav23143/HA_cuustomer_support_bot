import os

import requests

api_key = os.environ["GROQ_API_KEY"]
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    models = response.json().get("data", [])
    print("Available Groq Models:")
    for model in models:
        print(f"- {model['id']}")
else:
    print("Error fetching models:", response.text)
