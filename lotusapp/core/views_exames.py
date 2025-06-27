from django.db.models import Avg
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Exame, NotaAvaliacao, NotaComposta, Resposta, Usuario
from .serializers import (
    CorrecaoRespostaSerializer,
    ExameSerializer,
    NotaCompostaSerializer,
    RespostaSerializer,
)


class ExameViewSet(viewsets.ModelViewSet):
    serializer_class = ExameSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo == Usuario.Tipo.PROFESSOR:
            return Exame.objects.filter(professor__usuario=user).select_related(
                'turma', 'professor'
            )
        elif user.tipo == Usuario.Tipo.ALUNO:
            return (
                Exame.objects.filter(turma__alunos_matriculados__usuario=user)
                .distinct()
                .select_related('turma')
            )
        return Exame.objects.none()

    @action(detail=True, methods=['post'])
    def liberar_notas(self, request, pk=None):
        exame = self.get_object()

        if exame.data_liberacao:
            return Response(
                {'error': 'Notas já liberadas para este exame'}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if exame.liberar_notas():
                return Response(
                    {'status': 'Notas liberadas com sucesso'}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Correções pendentes para questões subjetivas'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {'error': f'Erro ao liberar notas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['get'])
    def preview_penalidades(self, request, pk=None):
        exame = self.get_object()
        if exame.tipo != 'TBL' or exame.fase != 'GRAT':
            return Response(
                {'error': 'Apenas exames gRAT suportam este recurso'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultados = []
        for equipe in exame.turma.equipes.all():
            try:
                nota_grat = NotaAvaliacao.objects.get(equipe=equipe, exame=exame, tipo='gRAT').valor

                media_irat = (
                    NotaAvaliacao.objects.filter(
                        aluno__in=equipe.alunos.all(), exame=exame.fase_associada, tipo='iRAT'
                    ).aggregate(media=Avg('valor'))['media']
                    or 0
                )

                nova_nota = NotaAvaliacao.aplicar_penalidade_grat(
                    nota_grat, media_irat, exame.fator_penalidade or 0.5
                )

                resultados.append(
                    {
                        'equipe': equipe.nome,
                        'nota_original': float(nota_grat),
                        'media_irat': float(media_irat),
                        'nova_nota': float(nova_nota),
                        'penalidade_aplicada': float(nota_grat - nova_nota),
                    }
                )
            except NotaAvaliacao.DoesNotExist:
                continue

        return Response(resultados)


class RespostaViewSet(viewsets.ModelViewSet):
    serializer_class = RespostaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        exame_id = self.kwargs.get('exame_pk')

        if user.tipo == Usuario.Tipo.ALUNO:
            return Resposta.objects.filter(
                aluno__usuario=user, questao__exame_id=exame_id
            ).select_related('questao', 'alternativa')
        return Resposta.objects.filter(questao__exame_id=exame_id).select_related(
            'questao', 'alternativa', 'aluno', 'equipe'
        )

    def create(self, request, *args, **kwargs):
        # Verificar prazo antes de criar
        exame_id = kwargs.get('exame_pk')
        try:
            exame = Exame.objects.get(pk=exame_id)
            if not exame.aberto:
                return Response(
                    {'error': 'Prazo para submissão expirado'}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exame.DoesNotExist:
            return Response({'error': 'Exame não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        questao = serializer.validated_data['questao']
        exame = questao.exame

        # Definir se é resposta individual ou de equipe
        if exame.tipo == 'TBL' and exame.fase == 'GRAT':
            try:
                equipe = user.aluno.equipes.get(turma=exame.turma)
                serializer.save(equipe=equipe)
            except Exception as e:
                raise serializers.ValidationError(f'Aluno não está em uma equipe válida: {str(e)}')
        else:
            serializer.save(aluno=user.aluno)


class CorrecaoViewSet(viewsets.ModelViewSet):
    serializer_class = CorrecaoRespostaSerializer
    permission_classes = [IsAuthenticated]
    queryset = Resposta.objects.filter(questao__tipo='SUB', corrigida=False).select_related(
        'questao__exame'
    )

    def get_queryset(self):
        if self.request.user.tipo == Usuario.Tipo.PROFESSOR:
            return self.queryset.filter(questao__exame__professor__usuario=self.request.user)
        return Resposta.objects.none()

    def perform_update(self, serializer):
        serializer.save(corrigida=True)

        # Verificar se todas as correções foram feitas
        exame = serializer.instance.questao.exame
        if not Resposta.objects.filter(
            questao__exame=exame, questao__tipo='SUB', corrigida=False
        ).exists():
            try:
                exame.liberar_notas()
            except Exception:
                # Não bloquear se falhar, apenas registrar
                pass


class NotaCompostaViewSet(viewsets.ModelViewSet):
    serializer_class = NotaCompostaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo == Usuario.Tipo.PROFESSOR:
            return NotaComposta.objects.filter(
                turma__professor_responsavel__usuario=user
            ).prefetch_related('componentes__exame')
        elif user.tipo == Usuario.Tipo.ALUNO:
            return NotaComposta.objects.filter(
                turma__alunos_matriculados__usuario=user
            ).prefetch_related('componentes__exame')
        return NotaComposta.objects.none()

    @action(detail=True, methods=['post'])
    def calcular(self, request, pk=None):
        nota_composta = self.get_object()
        try:
            nota_composta.calcular_para_todos()
            return Response(
                {'status': 'Notas compostas calculadas para todos os alunos'},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao calcular notas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
