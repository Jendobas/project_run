import openpyxl
from django.db.models import Sum
from django.forms import model_to_dict
from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from geopy import Point
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView

from app_run.models import Run, AthleteInfo, Challenge, Position, CollectibleItem
from app_run.serializers import RunSerializer, UserSerializer, RunStatus, AthleteInfoSerializer, ChallengeSerializer, \
    PositionSerializer, CollectibleSerializer, UserDetailSerializer
from geopy.distance import geodesic


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


def count_distance(run_id):
    # запускается после stop забега и высчитывает расстояние, которое побежал атлет
    distance_field = Run.objects.get(pk=run_id)
    positions = Position.objects.filter(run__id=run_id)
    points = []
    for position in positions:
        points.append((position.latitude, position.longitude))

    distance = geodesic(*points).kilometers

    distance_field.distance = distance
    distance_field.save()


def search_collectible(coordinates):
    collectible_items = CollectibleItem.objects.all()
    current_point = Point(coordinates['latitude'], coordinates['longitude'])

    for i in collectible_items:
        point = (i.latitude, i.longitude)
        distance_between_two_points = geodesic(current_point, point).kilometers

        if distance_between_two_points < 0.1:
            run = Run.objects.get(id=coordinates['run'])
            user = User.objects.get(username=run)
            i.users.add(user)


def check_50_km(run_id):
    item = Run.objects.get(pk=run_id).athlete
    sum = Run.objects.filter(athlete=item).aggregate(Sum('distance'))
    challenge = Challenge.objects.filter(athlete=item)
    for i in challenge:
        if i.full_name == 'Пробеги 50 километров!':
            return
    if sum['distance__sum'] >= 50:
        new_challange = Challenge.objects.create(
            full_name='Пробеги 50 километров!',
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

    def get_serializer_class(self):
        # Возвращаем базовый сериализатор для метода list
        if self.action == 'list':
            return UserSerializer
        # Возвращаем детализированный сериализатор для метода retrieve
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return super().get_serializer_class()

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
                count_distance(run_id)
                check_50_km(run_id)
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
                qs = qs.filter(athlete=athlete)
            return qs


class PositionViewSet(viewsets.ModelViewSet):
    # принимаем и записываем широту и долготу - координаты забега
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['run']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            coordinates = request.data
            search_collectible(coordinates)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectibleView(viewsets.ModelViewSet):
    # вернёт список CollectibleItem из БД
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleSerializer


class UploadFileView(viewsets.ModelViewSet):
    # view принимает xlsx-файл, читает, валидирует его и записывает эти данные в базу
    # неправильные строки записывает в broken_lines и возвращает в виде списка списков
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleSerializer

    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')  # получаем файл из запроса
        # поле в присланном request-e мы назвали file (выше)
        workbook = openpyxl.load_workbook(file)  # открывает Excel файл
        sheet = workbook.active
        broken_lines = []

        for row in sheet.iter_rows(values_only=True, min_row=2):
            row_data = {
                'name': row[0],
                'uid': row[1],
                'value': row[2],
                'latitude': row[3],
                'longitude': row[4],
                'picture': row[5]
            }

            serializer = self.get_serializer(data=row_data)

            if serializer.is_valid():
                serializer.save()
            else:
                broken_lines.append(list(row))

        return Response(broken_lines)
