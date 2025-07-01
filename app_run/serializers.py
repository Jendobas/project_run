from rest_framework import serializers
from .models import Run
from django.contrib.auth.models import User


class UserForRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = UserForRunSerializer(source='athlete', read_only=True)

    class Meta:
        model = Run
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username', 'last_name', 'first_name', 'type']

    def get_type(self, obj):
        if obj.is_staff:
            return 'coach'
        return 'athlete'


class RunStatus(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = ['id', 'athlete', 'status']
