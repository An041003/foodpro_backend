from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from .utils import generate_full_week_workout, generate_workout_plan_with_gemini
from .serializers import WorkoutPlanSerializer
from datetime import date
from .models import UserProfile
from .serializers import UserProfileSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken  
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
from .models import WorkoutPlan, Exercise, ExerciseLibrary
from rest_framework.generics import ListAPIView
from .serializers import ExerciseLibrarySerializer
from .ai_meal import generate_meal_plan_with_gemini, generate_alternative_dish_with_gemini
from django.http import JsonResponse
from django.views.generic import TemplateView

class FrontendAppView(TemplateView):
    template_name = '../frontend/dist/index.html'
    
def index(request):
    return JsonResponse({"message": "Welcome to the API"})


class RegisterView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        full_name = request.data.get("full_name")
        birthdate = request.data.get("birthdate")

        # Chỉ số
        height = request.data.get("height")
        weight = request.data.get("weight")
        waist = request.data.get("waist")
        neck = request.data.get("neck")
        hip = request.data.get("hip")
        gender = request.data.get("gender")

        if User.objects.filter(username=email).exists():
            return Response({"error": "Email đã tồn tại"}, status=400)

        user = User.objects.create(
            username=email,
            email=email,
            password=make_password(password),
        )

        UserProfile.objects.create(
            user=user,
            full_name=full_name,
            birthdate=birthdate,
            gender=gender,
            height=height,
            weight=weight,
            waist=waist,
            neck=neck,
            hip=hip,
        )

        # Tính BMI
        bmi = float(weight) / ((float(height) / 100) ** 2)
        if bmi < 18.5:
            goal = "Tăng cơ"
        elif bmi > 25:
            goal = "Giảm mỡ"
        else:
            goal = "Duy trì"

        generate_full_week_workout(user, bmi, gender, goal)
        return Response({"message": "Đăng ký + chỉ số thành công ✅"}, status=201)
    
class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(username=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({"message": "Đăng nhập thành công",
                             "access": str(refresh.access_token),
                             "refresh": str(refresh),
                             "user_id": user.id}, status=200)
        else:
            return Response({"error": "Tài khoản hoặc mật khẩu không đúng"}, status=400)       

class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if user.is_anonymous:
            raise NotAuthenticated("Bạn chưa đăng nhập.")
        return UserProfile.objects.get(user=user)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class WorkoutByDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        query_date = request.query_params.get("date")

        try:
            if query_date:
                target_date = date.fromisoformat(query_date)
            else:
                target_date = date.today()
        except ValueError:
            return Response({"error": "Định dạng ngày không hợp lệ (YYYY-MM-DD)"}, status=400)

        try:
            workout = WorkoutPlan.objects.get(user=user, date=target_date)
        except WorkoutPlan.DoesNotExist:
            return Response({
        "exercises": [], 
        "message": "Không có bài tập cho ngày này (có thể là ngày nghỉ)"
    }, status=200)

        serializer = WorkoutPlanSerializer(workout)
        return Response(serializer.data)    
    
class WorkoutResetView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("👉 request.data:", request.data)
        user = request.user
        goal = request.data.get("goal")  # "Tăng cơ", "Duy trì", "Giảm mỡ"
        gender = user.userprofile.gender
        height = user.userprofile.height
        weight = user.userprofile.weight

        if goal not in ["Tăng cơ", "Duy trì", "Giảm mỡ"]:
            return Response({"error": "Mục tiêu không hợp lệ"}, status=400)

        try:
            bmi = round(float(weight) / ((float(height) / 100) ** 2), 2)
        except:
            return Response({"error": "Không tính được BMI"}, status=400)

        # Xoá toàn bộ lịch tập cũ
        WorkoutPlan.objects.filter(user=user).delete()

        # Sinh lịch tập mới bằng AI Gemini
        generate_full_week_workout(user, bmi, gender, goal)

        return Response({
            "message": f"✅ Đã tạo lịch tập mới bằng AI theo mục tiêu: {goal}"
        }, status=200)  
    
class WorkoutRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        raw_date = request.data.get("date")
        mode = request.data.get("mode")
        gender = user.userprofile.gender

        if not raw_date:
            return Response({"error": "Thiếu ngày"}, status=400)

        try:
            target_date = date.fromisoformat(raw_date)
        except ValueError:
            return Response({"error": "Định dạng ngày sai"}, status=400)

        # Xoá hoặc tạo buổi tập
        workout, _ = WorkoutPlan.objects.get_or_create(
            user=user, date=target_date,
            defaults={"name": f"Buổi tập {target_date}", "mode": mode}
        )
        workout.mode = mode
        workout.name = f"Buổi tập {target_date} ({mode})"
        workout.save()

        # Xoá bài tập cũ
        workout.exercises.all().delete()

        # Lấy bài tập mới từ ExerciseLibrary
        candidates = ExerciseLibrary.objects.filter(mode=mode, gender__in=[gender, "any"]).order_by('?')[:4]
        for ex in candidates:
            Exercise.objects.create(
                workout=workout,
                name=ex.name,
                muscle_group=ex.muscle_group,
                video_id=ex.video_id,
                sets=4,
                reps="10-12",
                rest=60,
            )

        return Response({
            "message": f"Đã đổi buổi tập ngày {target_date}",
            "plan_id": workout.id
        }, status=200)   
    
class ReplaceExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        new_id = request.data.get("new_exercise_id")

        try:
            workout = WorkoutPlan.objects.get(pk=pk, user=user)
        except WorkoutPlan.DoesNotExist:
            return Response({"error": "Buổi tập không tồn tại"}, status=404)

        try:
            new_ex = ExerciseLibrary.objects.get(pk=new_id)
        except ExerciseLibrary.DoesNotExist:
            return Response({"error": "Bài tập mới không tồn tại"}, status=400)

        # Xóa toàn bộ bài tập cũ
        workout.exercises.all().delete()

        # Thêm bài tập mới duy nhất
        Exercise.objects.create(
            workout=workout,
            name=new_ex.name,
            muscle_group=new_ex.muscle_group,
            video_id=new_ex.video_id,
            sets=4,
            reps="10-12",
            rest=60,
        )

        return Response({"message": "Đã thay toàn bộ bài tập bằng bài mới ✅"})

class AddExerciseToWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        lib_id = request.data.get("exercise_id")

        try:
            workout = WorkoutPlan.objects.get(pk=pk, user=user)
        except WorkoutPlan.DoesNotExist:
            return Response({"error": "Không tìm thấy buổi tập"}, status=404)

        try:
            lib_ex = ExerciseLibrary.objects.get(pk=lib_id)
        except ExerciseLibrary.DoesNotExist:
            return Response({"error": "Bài tập không tồn tại"}, status=404)

        new_ex = Exercise.objects.create(
            workout=workout,
            name=lib_ex.name,
            muscle_group=lib_ex.muscle_group,
            video_id=lib_ex.video_id,
            sets=4,
            reps="10-12",
            rest=60,
        )

        return Response({
            "message": "Đã thêm bài tập thành công",
            "exercise_id": new_ex.id
        }, status=200)
    
class DeleteExerciseFromWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, workout_id, exercise_id):
        user = request.user

        try:
            workout = WorkoutPlan.objects.get(pk=workout_id, user=user)
        except WorkoutPlan.DoesNotExist:
            return Response({"error": "Buổi tập không tồn tại"}, status=404)

        try:
            exercise = workout.exercises.get(pk=exercise_id)
        except Exercise.DoesNotExist:
            return Response({"error": "Bài tập không thuộc buổi này"}, status=400)

        exercise.delete()
        return Response({"message": "Đã xoá bài tập thành công ✅"})

class ExerciseLibraryListView(ListAPIView):
    serializer_class = ExerciseLibrarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ExerciseLibrary.objects.all()
        mode = self.request.query_params.get("mode")
        muscle = self.request.query_params.get("muscle_group")
        gender = self.request.query_params.get("gender")

        if mode:
            qs = qs.filter(mode=mode)
        if muscle:
            qs = qs.filter(muscle_group__iexact=muscle)
        if gender:
            qs = qs.filter(gender__in=["any", gender])

        return qs

class AIGenerateMealView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("👉 request.data:", request.data)
        gender = request.data.get("gender", "male")
        bmi = float(request.data.get("bmi", 22))
        goal = request.data.get("goal", "Tăng cơ")

        base_meal = generate_meal_plan_with_gemini(gender, bmi, goal)
        if not base_meal:
            return Response({"error": "Không tạo được thực đơn từ Gemini"}, status=500)
        
        return Response(base_meal)

class AIDishSubstituteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        dish = request.data.get("dish")
        meal = request.data.get("meal")
        goal = request.data.get("goal")

        result = generate_alternative_dish_with_gemini(dish, meal, goal)
        return Response(result)

class AIGenerateWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("👉 request.data:", request.data)
        gender = request.user.userprofile.gender
        bmi = request.user.userprofile.bmi
        goal = request.data.get("goal", "Tăng cơ")
        muscle_group = request.data.get("muscle_group", "")
        date = request.data.get("date")

        if not date:
            return Response({"error": "Thiếu ngày"}, status=400)

        ai_plan = generate_workout_plan_with_gemini(gender, bmi, goal, muscle_group)
        if not ai_plan:
            return Response({"error": "Không tạo được lịch tập từ Gemini"}, status=500)

        # Xoá lịch tập cũ nếu có
        WorkoutPlan.objects.filter(user=request.user, date=date).delete()

        # Tạo mới lịch tập
        workout = WorkoutPlan.objects.create(
            user=request.user,
            date=date,
            name=f"Buổi tập AI - {goal}",
            mode="ai"
        )

        for ex in ai_plan:
            Exercise.objects.create(
                workout=workout,
                name=ex["name"],
                muscle_group=ex["muscle_group"],
                video_id=ex["video_id"],
                sets=ex["sets"],
                reps=ex["reps"],
                rest=ex["rest"],
            )

        return Response({"message": "Đã tạo buổi tập bằng AI", "plan_id": workout.id})
##