from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views_exames import (
    CorrecaoViewSet,
    ExameViewSet,
    NotaCompostaViewSet,
    NotaViewSet,
    RespostaViewSet,
    ResultadoNotaCompostaViewSet,
)

# Router para as viewsets de avaliação
avaliacao_router = DefaultRouter()
avaliacao_router.register(r'exames', ExameViewSet, basename='exame')
avaliacao_router.register(r'correcoes', CorrecaoViewSet, basename='correcao')
avaliacao_router.register(r'notas', NotaViewSet, basename='nota')
avaliacao_router.register(r'notas-compostas', NotaCompostaViewSet, basename='notacomp')
avaliacao_router.register(
    r'resultados-notas-compostas', ResultadoNotaCompostaViewSet, basename='resultadonotacomp'
)

urlpatterns = [
    # Endpoints existentes
    path('login/', views.login, name='login'),
    path('register/', views.cadastro, name='register'),
    path('professores/<int:id>/', views.info_perfil_prof, name='info_perfil_prof'),
    path('professores/<int:id>/turmas', views.listar_turmas_prof, name='listar_turmas_prof'),
    path('professores/<int:id>/casos', views.listar_casos_prof, name='listar_casos_prof'),
    path('professores/<int:prof_id>/casos/<int:caso_id>', views.info_casos, name='info_casos'),
    path('turmas/<int:id>', views.info_turmas, name='info_turmas'),
    # Novos endpoints para o sistema de avaliação
    path('avaliacao/', include(avaliacao_router.urls)),
    # Endpoint específico para respostas (aninhado em turma/exame)
    path(
        'turmas/<int:turma_pk>/exames/<int:exame_pk>/respostas/',
        RespostaViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='resposta-list',
    ),
]
