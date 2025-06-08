import time
import yaml
import json
from datetime import datetime
from julep import Julep

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

# --- Configuration ---
# IMPORTANT: Replace with your actual, valid Julep API key
JULEP_API_KEY = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiNjUyMjI0Yi1hNWQ3LTU2ZGItYTVhZS1kNzRkOTBjNjU3YTkiLCJlbWFpbCI6Im1hbnlham9zaGkxNTA3QGdtYWlsLmNvbSIsImlhdCI6MTc0OTMxNTkyOSwiZXhwIjoxNzQ5OTIwNzI5fQ.7U2xYKDj9FxXwS5wh7uWOUWOh8vKbmQsph-U-507Qwti7WsHsSOvvTNhj34UZI0qIiTYokHz2nmuGDtNce7AXA"
# IMPORTANT: Your OpenWeatherMap API Key
OPENWEATHERMAP_API_KEY = "a504af64fa7763b3c61303bff10120d9"

# --- CONFIGURABLE PARAMETERS ---
cities = ["Rome"]
diet_options = ["vegetarian", "vegan", "non-vegetarian", "gluten-free", "keto"]
mood_options = ["romantic", "adventurous", "casual", "luxury", "family-friendly", "business"]

# Make these configurable
diet = "vegetarian"  # Change this to any option from diet_options
mood = "romantic"    # Change this to any option from mood_options

print(f"Planning {mood} {diet} food tour for: {', '.join(cities)}")

# --- Initialize Julep Client ---
client = Julep(api_key=JULEP_API_KEY)

print("--- Starting Julep AI Food Tour Planner ---")

# --- Step 1: Create Dish Explorer Agent ---
print("\n--- Creating Dish Explorer Agent ---")
agent1 = client.agents.create(
    name="Dish Explorer",
    model="claude-3.5-sonnet",
    about=f"An AI that finds top {diet} dishes and where to eat them in any city, considering {mood} dining preferences."
)
print(f"✅ Dish Explorer Agent created with ID: {agent1.id}")

# --- Step 2: Define Dish and Restaurant Finder Task ---
print("\n--- Defining Dish and Restaurant Finder Task ---")
dish_task_yaml = f"""
name: Dish and Restaurant Finder
description: Given a city name, return top local {diet} dishes and matching restaurants
input_schema:
  type: object
  properties:
    city:
      type: string
    dietary_preference:
      type: string
    mood:
      type: string
  required: [city, dietary_preference, mood]
main:
  - prompt:
      - role: system
        content: You are a food critic helping people discover the best {diet} dishes and where to eat them, with a focus on {{{{steps[0].input.mood}}}} dining experiences.
      - role: user
        content: |
          What are the top {{{{steps[0].input.dietary_preference}}}} dishes to try in {{{{steps[0].input.city}}}}, and which restaurants serve them best? 
          Focus on options that would be suitable for a {{{{steps[0].input.mood}}}} dining experience.
          
          IMPORTANT: Only suggest dishes that are strictly {{{{steps[0].input.dietary_preference}}}}.
          
          Format your reply as:

          Dishes:
          - Dish Name 1: Short description (suitable for {{{{steps[0].input.mood}}}} dining)
          - Dish Name 2: Short description (suitable for {{{{steps[0].input.mood}}}} dining)
          - Dish Name 3: Short description (suitable for {{{{steps[0].input.mood}}}} dining)

          Restaurants:
          - Restaurant 1: Known for Dish X, located in Y, {{{{steps[0].input.mood}}}} atmosphere
          - Restaurant 2: Known for Dish Z, located in A, {{{{steps[0].input.mood}}}} atmosphere
          - Restaurant 3: Known for Dish W, located in B, {{{{steps[0].input.mood}}}} atmosphere
"""

dish_task_def = yaml.safe_load(dish_task_yaml)
dish_task = client.tasks.create(agent_id=agent1.id, **dish_task_def)
print(f"✅ Dish and Restaurant Finder Task created with ID: {dish_task.id}")

# --- Step 3: Run Dish Discovery for each city ---
print("\n--- Running Dish Discovery for each city ---")
city_dish_data_raw = []
for city in cities:
    print(f"🌆 Running discovery for: {city}")
    exec_result = client.executions.create(
        task_id=dish_task.id, 
        input={
            "city": city,
            "dietary_preference": diet,
            "mood": mood
        }
    )
    print(f"   Execution ID for {city}: {exec_result.id}")

    while True:
        result = client.executions.get(exec_result.id)
        if result.status in ["succeeded", "failed"]:
            break
        print(f"   Waiting for {city} result (Current Status: {result.status})...")
        time.sleep(2)

    if result.status == "succeeded":
        dish_output = result.output
        if isinstance(dish_output, dict) and 'choices' in dish_output and len(dish_output['choices']) > 0:
            formatted_dish_output = dish_output['choices'][0]['message']['content']
        else:
            formatted_dish_output = str(dish_output)

        city_dish_data_raw.append({
            "city": city,
            "dishes_and_restaurants": formatted_dish_output
        })
        print(f"✅ Succeeded for {city}. Output snippet:\n{formatted_dish_output[:200]}...\n")
    else:
        print(f"❌ Failed to fetch for {city}. Status: {result.status}, Error: {result.error}\n")

print("\n--- All City Dish Discovery Completed ---")

# --- Step 4: Create Meal Planner Agent ---
print(f"\n--- Creating {mood.title()} {diet.title()} Meal Planner Agent ---")
agent2 = client.agents.create(
    name=f"{mood.title()} {diet.title()} Meal Planner",
    model="gpt-4o",
    about=f"Suggests {mood}, {diet} food plans for cities based on local dishes, restaurants, and current weather conditions."
)
print(f"✅ {mood.title()} {diet.title()} Meal Planner Agent created with ID: {agent2.id}")

# --- Step 5: Define the Food Tour Planner Task (with proper Weather Integration) ---
print("\n--- Defining Food Tour Planner Task (with Weather Integration) ---")
plan_task_yaml = f"""
name: Food Tour Planner with Weather
description: Plan {mood} {diet} meals in cities based on local dishes, restaurants, and current weather conditions.
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
          dishes_and_restaurants:
            type: string
        required: [city, dishes_and_restaurants]
    dietary_preference:
      type: string
    mood:
      type: string
  required: [city_data, dietary_preference, mood]

tools:
- name: weather
  type: integration
  integration:
    provider: weather
    setup:
      openweathermap_api_key: {OPENWEATHERMAP_API_KEY}

main:
  # Step 1: Fetch weather for all cities.
  - over: $ steps[0].input.city_data
    map:
      tool: weather
      arguments:
        location: $ _.city
    
  # Step 2: Zip city data and weather results into a single list of tuples.
  - evaluate:
      zipped_data: $ list(zip(steps[0].input.city_data, steps[1]))

  # Step 3: Loop over the zipped_data, generate a plan for each, and unwrap to a list of strings.
  # We add 'parallelism' as shown in the documentation.
  - over: $ _['zipped_data']
    parallelism: 3
    map:
      prompt:
        - role: system
          content: >-
            You are a highly skilled food and travel guide specializing in creating **{{{{steps[0].input.mood}}}}, STRICTLY {{{{steps[0].input.dietary_preference}}}}** culinary experiences.
            Your task is to create a detailed day plan based on the city, cuisine list, and live weather. Your output should start with a clear title for the city.

            **Critical Instructions:**
            1.  **Weather is Key:** You MUST analyze the weather text (e.g., "rainy, 32°C") and explicitly use it in your suggestions.
            2.  **Adherence:** Strictly follow the **{{{{steps[0].input.dietary_preference}}}}** diet and **{{{{steps[0].input.mood}}}}** mood.
            3.  **Structure:** For Breakfast, Lunch, and Dinner, provide the **Dish**, **Restaurant**, and a **Narrative**.

        - role: user
          content: >-
            Please create a complete **{{{{steps[0].input.mood}}}} {{{{steps[0].input.dietary_preference}}}}** food tour plan for **{{{{ _[0].city }}}}**.
            
            **Available Dishes and Restaurants:**
            {{{{ _[0].dishes_and_restaurants }}}}
            
            **Current Weather Conditions:** {{{{ str(_[1]) }}}}
      unwrap: true

  # Step 4: Join the list of plans from Step 3 into a single final string.
  - evaluate:
      final_plan: |-
        $ '\\n\\n============================================================\\n\\n'.join(plan for plan in _)
"""

plan_task_def = yaml.safe_load(plan_task_yaml)
plan_task = client.tasks.create(agent_id=agent2.id, **plan_task_def)
print(f"✅ Food Tour Planner Task (with Weather) created with ID: {plan_task.id}")

# --- Step 6: Run the Final Planner Task ---
print("\n--- Running Final Food Tour Planner Task ---")
final_task_input = {
    "city_data": city_dish_data_raw,
    "dietary_preference": diet,
    "mood": mood
}

print("Input for final planner task:")
print(f"Cities: {[city['city'] for city in city_dish_data_raw]}")
print(f"Dietary Preference: {diet}")
print(f"Mood: {mood}")

final_exec = client.executions.create(
    task_id=plan_task.id,
    input=final_task_input
)
print(f"Final Planner Execution ID: {final_exec.id}")

# --- Monitor Execution Status ---
print("\n--- Monitoring Execution Progress ---")
while True:
    result = client.executions.get(final_exec.id)
    if result.status in ["succeeded", "failed"]:
        break
    print(f"🕑 Waiting for final plan (Current Status: {result.status})...")
    time.sleep(3)

# --- Display Results ---
if result.status == "succeeded":
    print(f"\n🎉 {mood.title()} {diet.title()} Food Tour Plan Complete!\n")
    
    # The output is now a dictionary with a single key 'final_plan'
    if isinstance(result.output, dict) and 'final_plan' in result.output:
        # We simply print the final, combined string.
        print(result.output['final_plan'])
    else:
        print("⚠️  The final output was not in the expected format. Raw result:")
        print(json.dumps(result.output, indent=2, cls=DateTimeEncoder))
        
else:
    print(f"\n❌ Final task failed. Status: {result.status}")
    if hasattr(result, 'error') and result.error:
        print(f"Error: {result.error}")
    print(f"\nFull failed execution result:")
    print(json.dumps(result.to_dict(), indent=2, cls=DateTimeEncoder))

# (The final print block with configuration details remains the same)

print(f"\n--- {mood.title()} {diet.title()} Food Tour Planner Finished ---")
print(f"Configuration used:")
print(f"  Cities: {cities}")
print(f"  Dietary Preference: {diet}")
print(f"  Mood: {mood}")
print(f"  Weather Integration: Enabled")