from rest_framework import serializers
from .models import UserProfile, WorkoutPlan, Exercise, ExerciseLibrary

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['body_fat', 'updated_at', 'bmi']
        extra_kwargs = {
            "user": {"read_only": True} 
        }

class ExerciseLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseLibrary
        fields = '__all__'


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'muscle_group', 'video_id', 'sets', 'reps', 'rest']


class WorkoutPlanSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True)

    class Meta:
        model = WorkoutPlan
        fields = ['id', 'user', 'date', 'name', 'mode', 'exercises']
        read_only_fields = ['user']

    def create(self, validated_data):
        exercises_data = validated_data.pop('exercises')
        workout = WorkoutPlan.objects.create(**validated_data)
        for ex_data in exercises_data:
            Exercise.objects.create(workout=workout, **ex_data)
        return workout

    def update(self, instance, validated_data):
        exercises_data = validated_data.pop('exercises', [])

        # Cập nhật thông tin cơ bản của buổi tập
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Xóa và thêm lại toàn bộ bài tập (có thể cải tiến sau)
        instance.exercises.all().delete()
        for ex_data in exercises_data:
            Exercise.objects.create(workout=instance, **ex_data)

        return instance
    
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email  
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user_id'] = self.user.id  
        return data
       
