from rest_framework import serializers
from .models import Run, AthleteInfo, Challenge
from django.contrib.auth.models import User


class UserForRunSerializer(serializers.ModelSerializer):
    # Этот сериалайзер будем вкладывать
    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = UserForRunSerializer(source='athlete',
                                        read_only=True)  # Добавляем UserForRunSerializer как вложенный

    # при использовании RunSerializer, API будет возвращать данные забега вместе с данными атлета
    class Meta:
        model = Run
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()  # позволяет динамически вычислять значение для этого поля
    runs_finished = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username', 'last_name', 'first_name', 'type', 'runs_finished']

    def get_type(self, obj):  # здесь будет вычисляться поле type
        if obj.is_staff:
            return 'coach'
        return 'athlete'

    def get_runs_finished(self, obj):
        return obj.runs.filter(status='finished').count()


class RunStatus(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = ['id', 'athlete', 'status']


class AthleteInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteInfo
        fields = ['user_id', 'goals', 'weight']


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['full_name', 'athlete']
