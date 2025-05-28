from django.urls import path
from .views import RegisterView, LoginView, ProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    MyTokenObtainPairView,
    WorkoutByDateView,
    WorkoutResetView,
    WorkoutRegenerateView,
    ReplaceExerciseView,
    AddExerciseToWorkoutView,
    DeleteExerciseFromWorkoutView,
    ExerciseLibraryListView,
    AIGenerateMealView,
    AIDishSubstituteView,
    AIGenerateWorkoutView,
    FrontendAppView,
)

urlpatterns = [
    path('', FrontendAppView.as_view()),
    path("auth/register/", RegisterView.as_view()),
    path('profile/', ProfileView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("workouts/", WorkoutByDateView.as_view()),
    path("workouts/reset/", WorkoutResetView.as_view()),
    path("workouts/generate/", WorkoutRegenerateView.as_view()),
    path("workouts/<int:pk>/replace-exercise/", ReplaceExerciseView.as_view()),
    path("workouts/<int:pk>/add-exercise/", AddExerciseToWorkoutView.as_view()),
    path("workouts/<int:workout_id>/exercise/<int:exercise_id>/", DeleteExerciseFromWorkoutView.as_view()),
    path("exercise-library/", ExerciseLibraryListView.as_view()),
    path("ai-meal-plan/", AIGenerateMealView.as_view(), name="ai_meal_plan"),
    path("ai-substitute-dish/", AIDishSubstituteView.as_view()),
    path("ai-generate-workout/", AIGenerateWorkoutView.as_view()),

]

