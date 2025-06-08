# Julep AI Food Tour Planner

This project demonstrates a multi-agent AI workflow built with Julep, designed to create personalized one-day "foodie tours" for specified cities. It intelligently combines local culinary recommendations with real-time weather conditions to suggest delightful dining experiences.

## Features

* **Dynamic City Selection:** Easily configure the list of cities for your food tour.
* **Personalized Dining (Mood & Dietary Focus):** This is a key added feature! You can tailor the food suggestions based on **dietary preferences** (e.g., vegetarian, vegan, non-vegetarian, gluten-free, keto) and your desired **dining mood** (e.g., romantic, adventurous, casual, luxury, family-friendly, business). The AI will strictly adhere to these choices when recommending dishes and restaurants.
* **Weather-Aware Planning:** Integrates live weather data to suggest appropriate indoor or outdoor dining options and weave weather conditions into the daily narrative.
* **Iconic Local Dishes:** Identifies and recommends 3 iconic local dishes per city, adhering strictly to the specified dietary preference.
* **Top-Rated Restaurant Discovery:** Finds highly-rated restaurants known for serving the recommended dishes, aligning with the chosen dining mood.
* **Delightful Foodie Tour Narratives:** Generates creative and engaging breakfast, lunch, and dinner narratives for each city, making the tour truly immersive.

## How It Works: The Julep Workflow

The workflow is orchestrated using two distinct Julep AI agents and several tasks, ensuring a modular and efficient process:

### 1. Dish Explorer Agent (Powered by Claude-3.5-Sonnet)

* **Purpose:** This agent is responsible for researching and identifying top local dishes that adhere to the specified `dietary_preference` and are suitable for the chosen `mood`. It also finds relevant restaurants.
* **Task: Dish and Restaurant Finder:**
    * **Input:** City name, dietary preference, and dining mood.
    * **Process:** Prompts the LLM (Claude-3.5-Sonnet) to act as a food critic, extracting top dishes and associated restaurants. Strict formatting ensures the output is easily parsable for the next stage.
    * **Output:** A structured text containing lists of recommended dishes with short descriptions and restaurants known for those dishes, along with their atmosphere.

### 2. Meal Planner Agent (Powered by GPT-4o)

* **Purpose:** This agent takes the dish and restaurant information, combines it with real-time weather data, and crafts the final one-day foodie tour narrative. It's designed to be a highly skilled food and travel guide.
* **Task: Food Tour Planner with Weather:**
    * **Inputs:**
        * `city_data`: A list of dictionaries, each containing a city and the raw `dishes_and_restaurants` output from the "Dish Explorer" agent.
        * `dietary_preference`: The chosen diet.
        * `mood`: The chosen dining mood.
    * **Tools:** Leverages Julep's **Weather Integration** tool (powered by OpenWeatherMap) to fetch current weather conditions for each city.
    * **Process:**
        1.  **Fetch Weather:** Iterates through each specified city to get its current weather using the `weather` tool.
        2.  **Combine Data:** Zips the initial city data (dishes/restaurants) with the fetched weather data for seamless integration.
        3.  **Generate Plan (in Parallel):** Loops over the combined city and weather data. For each city, it prompts the GPT-4o model to:
            * Act as a food and travel guide, specializing in the chosen `mood` and `dietary_preference`.
            * **Crucially, analyze the weather conditions** and explicitly incorporate them into the dining suggestions (e.g., "Given the rainy weather, we suggest an intimate indoor setting...").
            * Create a detailed plan with **Breakfast, Lunch, and Dinner**, providing a **Dish**, **Restaurant**, and a **Narrative** for each.
            * `parallelism: 3` is used to speed up the generation of plans for multiple cities concurrently.
        4.  **Final Assembly:** Concatenates all individual city plans into a single, cohesive food tour document.
    * **Output:** A comprehensive string detailing the one-day food tour for each city, incorporating weather-aware recommendations and delightful narratives.

## Getting Started

### Prerequisites

* **Julep API Key:** Obtain your API key from the Julep dashboard.
* **OpenWeatherMap API Key:** Register for a free API key on the OpenWeatherMap website.

### Configuration

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-link>
    cd <your-repo-directory>
    ```
2.  **Install Dependencies:**
    ```bash
    pip install julep pyyaml
    ```
3.  **Set API Keys:**
    Replace the placeholder values in the `JULEP_API_KEY` and `OPENWEATHERMAP_API_KEY` variables at the top of the `final.py` file with your actual keys.
    ```python
    JULEP_API_KEY = "YOUR_JULEP_API_KEY_HERE"
    OPENWEATHERMAP_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY_HERE"
    ```
4.  **Configure Tour Preferences:**
    Adjust the `cities`, `diet`, and `mood` variables to customize your food tour. These directly influence the recommendations generated by the AI:
    ```python
    cities = ["Rome", "Tokyo", "New York"] # Add or remove cities as desired
    diet = "vegetarian"                  # Choose from diet_options: "vegetarian", "vegan", "non-vegetarian", "gluten-free", "keto"
    mood = "romantic"                    # Choose from mood_options: "romantic", "adventurous", "casual", "luxury", "family-friendly", "business"
    ```

### Running the Workflow

Execute the Python script:

```bash
python final.py
```
The script will print the progress of agent and task creation, execution, and finally, the complete food tour plan directly to your console.

---

### Example Output

An example of the generated food tour plan for the predefined parameters (e.g., `cities = ["Rome"]`, `diet = "vegetarian"`, `mood = "romantic"`) can be found in `output.txt`. This file provides a concrete illustration of the AI's output format and content.
