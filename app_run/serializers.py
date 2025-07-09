from rest_framework import serializers
from .models import Run
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

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username', 'last_name', 'first_name', 'type']

    def get_type(self, obj):  # здесь будет вычисляться поле type
        if obj.is_staff:
            return 'coach'
        return 'athlete'


class RunStatus(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = ['id', 'athlete', 'status']
