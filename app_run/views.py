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

from app_run.models import Run, AthleteInfo
from app_run.serializers import RunSerializer, UserSerializer, RunStatus, AthleteInfoSerializer


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
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AthleteInfoView(APIView):

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
        if int(request.data['weight']) < 0 or int(request.data['weight']) >= 900:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        athlete_more_info, _ = AthleteInfo.objects.update_or_create(user_id_id=user.id,
                                                                    defaults={'goals': request.data['goals'],
                                                                              'weight': request.data['weight']})
        serializer = AthleteInfoSerializer(athlete_more_info, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

