from rest_framework import serializers
from .models import Run, AthleteInfo, Challenge, Position, CollectibleItem
from django.contrib.auth.models import User


class UserForRunSerializer(serializers.ModelSerializer):
    # Этот сериалайзер будем вкладывать в RunSerializer
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
        return obj.runs_finished
        # return obj.runs.filter(status='finished').count()


class UserDetailSerializer(UserSerializer):  # дополнительный сериалайзер для GetUsers
    items = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ['items']

    def get_items(self, obj):  # здесь будет вычисляться поле items
        return [
            {
                'name': item.name,
                'uid': item.uid,
                'value': item.value,
                'latitude': item.latitude,
                'longitude': item.longitude,
                'picture': item.picture
            }
            for item in obj.collectible_items.all()
        ]


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


class PositionSerializer(serializers.ModelSerializer):
    date_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%f')

    class Meta:
        model = Position
        fields = '__all__'

    def validate_run(self, value):
        run_status = Run.objects.get(id=value.id).status
        if run_status != 'in_progress':
            raise serializers.ValidationError("Статус забега должен быть 'in progress'")
        return value

    def validate_latitude(self, value):
        if not -90.0 <= value <= 90.0:
            raise serializers.ValidationError("latitude от -90.0 до +90.0")
        return value

    def validate_longitude(self, value):
        if not -180.0 <= value <= 180.0:
            raise serializers.ValidationError("longitude от -180.0 до +180.0")
        return value


class CollectibleSerializer(serializers.ModelSerializer):
    picture = serializers.URLField()

    class Meta:
        model = CollectibleItem
        fields = ['name', 'uid', 'value', 'latitude', 'longitude', 'picture']

    def validate_latitude(self, value):
        if not -90.0 <= value <= 90.0:
            raise serializers.ValidationError("latitude от -90.0 до +90.0")
        return value

    def validate_longitude(self, value):
        if not -180.0 <= value <= 180.0:
            raise serializers.ValidationError("longitude от -180.0 до +180.0")
        return value
