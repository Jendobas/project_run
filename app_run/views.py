from django.forms import model_to_dict
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView

from app_run.models import Run
from app_run.serializers import RunSerializer, UserSerializer, RunStatus


@api_view(['GET'])
def company_details(request):
    return Response({
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS
    })


class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.select_related('athlete').all()
    serializer_class = RunSerializer


class GetUsers(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = UserSerializer

    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name']

    def get_queryset(self):
        qs = self.queryset
        type = self.request.query_params.get('type')
        if type == 'coach':
            qs = qs.filter(is_staff=True)
        elif type == 'athlete':
            qs = qs.filter(is_staff=False)
        return qs


class StartView(APIView):

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
