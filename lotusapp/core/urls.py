from django.urls import path
from . import views
urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.cadastro, name='register'),
    path('professores/<int:id>/', views.info_perfil_prof, name='info_perfil_prof'),
]
