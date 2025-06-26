from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def company_details(request):
    return Response({
        'company_name': 'Ночной забег',
        'slogan': 'Ноль - тоже результат',
        'contacts': 'Город Москва, улица Пушкина, дом 3'
    })
