import requests
from julep import Client
import uuid
import time
import yaml
import json
from scrapegraphai.graphs import SmartScraperGraph

# ---- API KEYS ----
JULEP_API_KEY = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiNjUyMjI0Yi1hNWQ3LTU2ZGItYTVhZS1kNzRkOTBjNjU3YTkiLCJpYXQiOjE3NDkyODUyNDUsImV4cCI6MTc1NDQ2OTI0NX0.531dKlPSYWqPFSnV6iaLLfgzBkjoNRX5K-no4UQFyT8CS-x07WEMOerQDsqH6VpwGiUcHKGIxIzQvVqHi9Qs8g"
WEATHER_API_KEY = "a504af64fa7763b3c61303bff10120d9"
SERPER_API_KEY = "b4571e3762d2602f18fe847c61dce87f1fc2ce7e"
GROQ_API_KEY = "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"

cities = ["Delhi", "Tokyo", "Rome"]
diet = "vegetarian"
mood = "romantic"

# ---- Helper Functions ----
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        return res['weather'][0]['description'] + f", Temp: {res['main']['temp']}°C"
    except:
        return "Weather info not available"

def get_top_urls(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    data = {"q": query}
    res = requests.post(url, headers=headers, json=data)
    if res.status_code != 200:
        return []
    return [item.get("link") for item in res.json().get("organic", [])[:8]]

def scrape_content_from_urls(urls, prompt):
    combined = []
    for url in urls:
        try:
            graph_config = {
                "llm": {
                    "api_key": GROQ_API_KEY,
                    "model": "gemma2-9b-it",
                },
                "verbose": False,
                "headless": True,
            }
            graph = SmartScraperGraph(prompt=prompt, source=url, config=graph_config)
            result = graph.run()
            combined.append(json.dumps(result))
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    return "\n".join(combined)

# ---- Collecting Data ----
city_data = []
for city in cities:
    print(f"🔍 Gathering data for {city}...")
    weather = get_weather(city)

    # SERPER → URLS
    dish_urls = get_top_urls(f"famous dishes in {city}")
    rest_urls = get_top_urls(f"{diet} restaurants in {city}")

    # SCRAPEGRAPH → TEXT BLOCKS
    dishes = scrape_content_from_urls(dish_urls, f"Extract famous dishes from this city: {city}")
    restaurants = scrape_content_from_urls(rest_urls, f"Extract good {diet} restaurants from this city: {city}")

    city_data.append((city, weather, dishes, restaurants))

# ---- Julep Part ----
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()
client = Client(api_key=JULEP_API_KEY, environment="production")

print("👤 Creating agent...")
client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Manya",
    about="A foodie assistant that plans meals based on weather, mood and dietary preference.",
    model="gpt-4o"
)

task_yaml = """
name: Food Tour Planner (Scrapegraph-enhanced)
input_schema:
  type: object
  properties:
    city_data:
      type: array
      items:
        type: object
        properties:
          city:
            type: string
          weather:
            type: string
          dishes:
            type: string
          restaurants:
            type: string
        required: [city, weather, dishes, restaurants]
    dietary_preference:
      type: string
    mood:
      type: string
  required: [city_data, dietary_preference, mood]

main:
  - over: $steps[0].input.city_data
    map:
      prompt:
        - role: system
          content: >-
            You are a foodie assistant. Based on the weather, dishes, and restaurants, plan a 3-meal romantic vegetarian food tour in this city.
        - role: user
          content: >-
            City: {{_.city}}
            Weather: {{_.weather}}
            Dishes Info: {{_.dishes}}
            Restaurants Info: {{_.restaurants}}
            Dietary Preference: {{steps[0].input.dietary_preference}}
            Mood: {{steps[0].input.mood}}
      unwrap: true

  - evaluate:
      final_plan: |
        $ '\\n---\\n'.join(_)
"""

task_def = list(yaml.safe_load_all(task_yaml))[0]

print("📋 Creating task...")
client.tasks.create_or_update(task_id=TASK_UUID, agent_id=AGENT_UUID, **task_def)

debug_input = {
    "city_data": [
        {"city": city, "weather": weather, "dishes": dishes, "restaurants": restaurants}
        for city, weather, dishes, restaurants in city_data
    ],
    "dietary_preference": diet,
    "mood": mood
}
print(json.dumps(debug_input, indent=2))

print("🚀 Running execution...")
execution = client.executions.create(
    task_id=TASK_UUID,
    input=debug_input
)

print(f"Execution started: {execution.id}")
print("⏳ Polling for result...")

while execution.status != "succeeded":
    time.sleep(5)
    execution = client.executions.get(execution.id)
    print(f"Status: {execution.status}")

print("📥 Execution output:")
print(json.dumps(execution.output, indent=2))

print("\n📍 Final Plan:\n")
print(execution.output.get("final_plan", execution.output))
