import os
import json
import requests

def parse_meal_plan_from_gemini(raw_json):
    structured = {}

    for meal in ["breakfast", "lunch", "dinner", "snack"]:
        meal_data = raw_json.get(meal, {})
        dishes = meal_data.get("dishes", [])
        total_nutrition = meal_data.get("total_nutrition", {})

        parsed_dishes = []
        for dish in dishes:
            parsed_dishes.append({
                "name": dish.get("name"),
                "ingredients": dish.get("ingredients", []),
                "nutrition": dish.get("nutrition", {}),
                "instruction": dish.get("cooking_instructions", "")
            })

        structured[meal] = {
            "dishes": parsed_dishes,
            "total_nutrition": total_nutrition
        }

    return structured

def generate_meal_plan_with_gemini(gender, bmi, goal):
    api_key = os.getenv("GEMINI_API_KEY")

    prompt = f"""
You are an AI nutritionist specializing in Vietnamese cuisine. Your job is to generate structured daily meal plans based on the user's health metrics.

 LANGUAGE: All outputs must be strictly in Vietnamese.
 FORMAT: Return only valid JSON, no explanation or markdown.

=== INPUT PARAMETERS ===
{{
  "gender": "{gender}",  
  "bmi": {bmi},
  "goal": "{goal}"
}}

=== REQUIREMENTS ===
- Daily meal plan with 3 main meals (breakfast, lunch, dinner) and 1 snack.
- Each meal contains 1–3 dishes.
- For each dish:
  • Vietnamese name (dishes)
  • Ingredients (Vietnamese, locally available)
  • Cooking instructions (3–4 concise Vietnamese sentences)
  • Nutrition facts per dish:
    - Calories (round to nearest 50)
    - Protein (g)
    - Carbs (g)
    - Fat (g)
- For each meal:
  • Total nutrition facts (sum of all dishes): calories, protein, carbs, fat

=== NUTRITION RULES BASED ON GOAL ===
- Tăng cơ → 2200–2500 kcal/day, high protein (>20g per meal)
- Duy trì → 1800–2200 kcal/day, moderate protein (15–20g/meal)
- Giảm mỡ → 1500–1800 kcal/day, low fat (<10g fat/meal)

=== OUTPUT FORMAT ===
```json
{{
  "breakfast": {{
    "dishes": [
      {{
        "name": "Bánh mì trứng ốp la",
        "ingredients": ["Bánh mì", "Trứng gà", "Dầu ô liu"],
        "nutrition": {{
          "calories": 350,
          "protein": 15.2,
          "carbs": 40,
          "fat": 12.5
        }},
        "cooking_instructions": "Chiên trứng với dầu ô liu. Nướng bánh mì giòn. Kẹp trứng vào bánh mì."
      }}
    ],
    "total_nutrition": {{
      "calories": 350,
      "protein": 15.2,
      "carbs": 40,
      "fat": 12.5
    }}
  }},
  "lunch": {{ ... }},
  "dinner": {{ ... }},
  "snack": {{ ... }}
}}
```
ONLY RETURN THE JSON. Do not include explanations or markdown. Ensure correct Vietnamese grammar and numeric values.
"""

    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )

        data = res.json()

        if "candidates" not in data:
            print("❌ Gemini API error:", data)
            return {}

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        if text.startswith("```json"):
            text = text.replace("```json", "").strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        raw_meal = json.loads(text)
        return parse_meal_plan_from_gemini(raw_meal)

    except Exception as e:
        print("❌ Lỗi khi gọi hoặc phân tích Gemini:", e)
        return {}

def generate_alternative_dish_with_gemini(dish_name, meal_type, goal):
    api_key = os.getenv("GEMINI_API_KEY")

    prompt = f"""
You are an AI nutritionist. Please suggest a Vietnamese dish that can replace the dish: "{dish_name}".

Requirements:
- For meals: {meal_type}
- Nutritional goal: {goal}
- Use common ingredients in Vietnam
- Include:

1. Name of dish

2. Ingredients (list format)

3. Brief cooking instructions (2-4 sentences)

4. Nutritional information: calories, protein, carbs, fat

Return correct JSON format as follows:
```json
{{
  "name": "Phở bò",
  "ingredients": ["Bánh phở", "Thịt bò", "Hành lá", "Nước dùng", "Gia vị"],
  "cooking_instructions": "Luộc bánh phở, nấu nước dùng với xương và gia vị. Trụng thịt bò, cho vào tô cùng bánh phở và chan nước dùng.",
  "nutrition": {{
    "calories": 450,
    "protein": 25,
    "carbs": 50,
    "fat": 15
  }}
}}
Just returns JSON, no further explanation needed.
"""

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )

        data = response.json()

        if "candidates" not in data:
            print("❌ Gemini API error:", data)
            return {}

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Xử lý nếu có markdown
        if text.startswith("```json"):
            text = text.replace("```json", "").strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        return json.loads(text)

    except Exception as e:
        print("❌ Lỗi khi gọi hoặc phân tích Gemini:", e)
        return {}
