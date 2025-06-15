from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.cadastro, name='register'),
    path('professores/<int:id>/', views.info_perfil_prof, name='info_perfil_prof'),
    path('professores/<int:id>/turmas', views.listar_turmas_prof, name='listar_turmas_prof'),
    path(
        'professores/<int:prof_id>/turmas/<int:turma_id>/equipes',
        views.listar_equipes,
        name='listar_equipes',
    ),
    path('professores/<int:id>/casos', views.listar_casos_prof, name='listar_casos_prof'),
    path('professores/<int:prof_id>/casos/<int:caso_id>', views.info_casos, name='info_casos'),
    path('turmas/<int:id>', views.info_turmas, name='info_turmas'),
]
