import os
import json
import requests
from datetime import date, timedelta
from .models import WorkoutPlan, Exercise

def generate_workout_plan_with_gemini(gender, bmi, goal, muscle_group):
    api_key = os.getenv("GEMINI_API_KEY")

    prompt = f"""
You are a Vietnamese personal trainer. Based on the user's gender, BMI, and fitness goal, generate a structured workout plan for 1 day.

LANGUAGE: All output must be strictly in Vietnamese(As for the names of the exercises, they should be in English, no need to annotate the names of the exercises in Vietnamese.).
FORMAT: Return only valid JSON, no explanation or markdown.

=== INPUT ===
- Gender: {gender}
- BMI: {bmi}
- Goal: {goal}
- Muscle group: {muscle_group}

=== REQUIREMENTS ===
-  3 to 5 exercises focused on the muscle group: {muscle_group}
- For each exercise:
  - "name": Vietnamese exercise name
  - "muscle_group": main muscle group targeted (in Vietnamese)
  - "video_id": YouTube video ID only (not full link, If Muscle group: "Nghỉ", suggest any entertaining video.)
  - "sets": integer (e.g., 4)
  - "reps": string (e.g., "10-12")
  - "rest": rest time in seconds

=== OUTPUT FORMAT ===
```json
[
  {{
    "name": "Push-up",
    "muscle_group": "Ngực",
    "video_id": "dQw4w9WgXcQ",
    "sets": 4,
    "reps": "10-12",
    "rest": 60
  }},
  ...
]
```

Only return the JSON data in Vietnamese.
"""

    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        data = res.json()

        if "candidates" not in data:
            print("\u274c Gemini API error:", data)
            return []

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Remove code block wrappers if present
        if text.startswith("```json"):
            text = text.replace("```json", "").strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        return json.loads(text)

    except Exception as e:
        print("\u274c Lỗi khi gọi hoặc phân tích Gemini:", e)
        return []

def generate_full_week_workout(user, bmi, gender, goal):
    api_key = os.getenv("GEMINI_API_KEY")

    prompt = f"""
You are a Vietnamese personal trainer. Based on the user's gender, BMI, and fitness goal, generate a 7-day workout schedule.

LANGUAGE: All output must be strictly in Vietnamese(As for the names of the exercises, they should be in English, no need to annotate the names of the exercises in Vietnamese.).
FORMAT: Return only valid JSON, no explanation or markdown.

=== INPUT ===
- Gender: {gender}
- BMI: {bmi}
- Goal: {goal}

=== REQUIREMENTS ===
- Generate 7 days of workouts, each focused on a specific major muscle group to avoid overlapping.
- Daily muscle group structure:

  1. Chủ nhật: Nghỉ ngơi(không tập luyện)
  2. Thứ hai: Ngực  
  3. Thứ ba: Lưng
  4. Thứ tư: Chân
  5. Thứ năm: Vai
  6. Thứ sáu: Tay
  7. Thứ bảy: Toàn thân

- For each workout day (except Sunday), include 3 to 5 exercises
- For each exercise:
  - "name": Vietnamese name
  - "muscle_group": main targeted muscle group (phù hợp với ngày đó)
  - "video_id": YouTube video ID only (If it's Sunday, suggest any entertaining video. )
  - "sets": integer (e.g., 4)
  - "reps": string (e.g., "10-12")
  - "rest": rest time in seconds


=== OUTPUT FORMAT ===
```json
[
  {{
    "day": "Thứ hai",
    "exercises": [
      {{
        "name": "Push-up",
        "muscle_group": "Ngực",
        "video_id": "dQw4w9WgXcQ",
        "sets": 4,
        "reps": "10-12",
        "rest": 60
      }},
      ...
    ]
  }},
  ...
]
```
Only return the JSON data in Vietnamese.
"""

    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        data = res.json()

        if "candidates" not in data:
            print("\u274c Gemini API error:", data)
            return

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        if text.startswith("```json"):
            text = text.replace("```json", "").strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        week_plan = json.loads(text)

        # Tính ngày bắt đầu (Chủ Nhật tuần hiện tại)
        today = date.today()
        start = today - timedelta(days=today.weekday() + 1) if today.weekday() < 6 else today

        for i, day_plan in enumerate(week_plan[:7]):
            workout_date = start + timedelta(days=i)
            exercises = day_plan.get("exercises", [])

            workout = WorkoutPlan.objects.create(
                user=user,
                date=workout_date,
                name=f"Buổi tập AI {i+1} ({goal})",
                mode="ai"
            )

            for ex in exercises:
                Exercise.objects.create(
                    workout=workout,
                    name=ex["name"],
                    muscle_group=ex["muscle_group"],
                    video_id=ex["video_id"],
                    sets=ex["sets"],
                    reps=ex["reps"],
                    rest=ex["rest"]
                )

    except Exception as e:
        print("\u274c Lỗi khi gọi hoặc phân tích Gemini:", e)