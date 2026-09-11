from django.urls import path
from . import views

app_name = 'exports'

urlpatterns = [
    path('<str:data_type>/', views.export_data, name='export-data'),
]
