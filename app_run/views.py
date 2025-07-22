from django.forms import model_to_dict
from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView

from app_run.models import Run, AthleteInfo, Challenge, Position
from app_run.serializers import RunSerializer, UserSerializer, RunStatus, AthleteInfoSerializer, ChallengeSerializer, \
    PositionSerializer


def check_runs(run_id):
    # проверяет, сделал ли атлет ровно 10 забегов, если да, то создается запись в таблице Challenge
    item = Run.objects.get(pk=run_id).athlete
    serializer = UserSerializer(item)
    count_runs = serializer.data['runs_finished']
    if count_runs == 10:
        new_challange = Challenge.objects.create(
            full_name='Сделай 10 Забегов!',
            athlete=item
        )
    new_challange.save()


@api_view(['GET'])
def company_details(request):
    return Response({
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS
    })


class RunPagination(PageNumberPagination):  # Настраиваем пагинацию в этом классе
    page_size_query_param = 'size'  # Разрешаем изменять количество объектов через query параметр size в url
    max_page_size = 50  # Ограничиваем максимальное количество объектов на странице


class RunViewSet(viewsets.ModelViewSet):
    # с select_related мы можем сделать один запрос для получения всех Run и User данных
    # так избавимся от проблемы n + 1
    queryset = Run.objects.select_related('athlete').all()
    serializer_class = RunSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]  # Указываем какой класс будет исп. для фильтра и сортировки
    filterset_fields = ['status', 'athlete']  # Поля, по которым будет происходить фильтрация
    ordering_fields = ['created_at']  # Поля, по которым будет возможна сортировка
    pagination_class = RunPagination  # Указываем пагинацию


class GetUsers(viewsets.ReadOnlyModelViewSet):
    # получаем всех пользователей, есть фильтр тренеры/атлеты
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = UserSerializer

    filter_backends = [SearchFilter, OrderingFilter]  # Подключаем SearchFilter здесь и сортировку
    search_fields = ['first_name', 'last_name']  # Указываем поля по которым будет вестись поиск
    ordering_fields = ['date_joined']
    pagination_class = RunPagination

    # Для динамической фильтрации данных будем переопределять метод get_queryset
    def get_queryset(self):
        qs = self.queryset
        type = self.request.query_params.get('type')
        if type == 'coach':
            qs = qs.filter(is_staff=True)
        elif type == 'athlete':
            qs = qs.filter(is_staff=False)
        return qs


class StartView(APIView):
    # создание статуса забега
    # принимаем 'start' значит забег 'in_progress'
    # принимаем 'stop' значит забег 'finished'

    def post(self, request, run_id, condition):
        item = get_object_or_404(Run, pk=run_id)
        condition_dict = {'start': 'in_progress', 'stop': 'finished'}
        if condition == 'start' and item.status in ['in_progress', 'finished']:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if condition == 'stop' and item.status != 'in_progress':
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if condition in condition_dict:
            item.status = condition_dict[condition]
        serializer = RunSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if condition == 'stop':
                check_runs(run_id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AthleteInfoView(APIView):
    # добавляет и изменяет записи в таб AthleteInfo о целях и весе бегуна
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        athlete_more_info, _ = AthleteInfo.objects.get_or_create(user_id_id=user.id, defaults={'goals': '',
                                                                                               'weight': 0})
        serializer = AthleteInfoSerializer(athlete_more_info, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        n = request.data['weight']
        if not n.isdigit() or int(n) <= 0 or int(n) >= 900:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        athlete_more_info, _ = AthleteInfo.objects.update_or_create(user_id_id=user.id,
                                                                    defaults={'goals': request.data['goals'],
                                                                              'weight': request.data['weight']})
        serializer = AthleteInfoSerializer(athlete_more_info, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class AllChallenges(viewsets.ModelViewSet):
    # возвращает список всех записей всех челленджей, если есть query,
    # то возвращает достижения конкретного атлета
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer

    def get_queryset(self):
        if self.queryset:
            qs = self.queryset
            athlete = self.request.query_params.get('athlete')
            if athlete:
                print(athlete)
                qs = qs.filter(athlete=athlete)
            return qs


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['run']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
