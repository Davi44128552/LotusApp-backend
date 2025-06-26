from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Exame, NotaAvaliacao, NotaComposta, Resposta, ResultadoNotaComposta, Usuario
from .serializers import (
    ComponenteNotaCompostaSerializer,
    CorrecaoRespostaSerializer,
    ExameSerializer,
    NotaCompostaSerializer,
    NotaSerializer,
    RespostaSerializer,
    ResultadoNotaCompostaSerializer,
)


class ExameViewSet(viewsets.ModelViewSet):
    serializer_class = ExameSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo == Usuario.Tipo.PROFESSOR:
            return Exame.objects.filter(professor__usuario=user)
        elif user.tipo == Usuario.Tipo.ALUNO:
            aluno = user.aluno
            turmas = aluno.turmas_matriculadas.all()
            return Exame.objects.filter(turma__in=turmas)
        return Exame.objects.none()

    @action(detail=True, methods=['post'])
    def liberar_notas(self, request, pk=None):
        exame = self.get_object()

        if exame.data_liberacao:
            return Response({'error': 'Notas já liberadas'}, status=status.HTTP_400_BAD_REQUEST)

        if exame.tipo == 'PBL':
            respostas_nao_corrigidas = exame.respostas.filter(
                questao__tipo='SUB', corrigida=False
            ).exists()

            if respostas_nao_corrigidas:
                return Response(
                    {'error': 'Correções pendentes para questões subjetivas'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            # TBL Exam Handling
            if exame.tipo == 'TBL':
                if exame.fase_tbl == 'iRAT':
                    for aluno in exame.turma.alunos_matriculados.all():
                        nota = self.calcular_nota_aluno(aluno, exame)
                        NotaAvaliacao.objects.update_or_create(
                            aluno=aluno, exame=exame, tipo='iRAT', defaults={'valor': nota}
                        )
                elif exame.fase_tbl == 'gRAT':
                    for equipe in exame.turma.equipes.all():
                        nota = self.calcular_nota_equipe(equipe, exame)
                        NotaAvaliacao.objects.update_or_create(
                            equipe=equipe, exame=exame, tipo='gRAT', defaults={'valor': nota}
                        )
            elif exame.tipo == 'PBL':
                for aluno in exame.turma.alunos_matriculados.all():
                    nota = self.calcular_nota_aluno(aluno, exame)
                    NotaAvaliacao.objects.update_or_create(
                        aluno=aluno, exame=exame, tipo='PBL', defaults={'valor': nota}
                    )

            # Release exam scores
            exame.data_liberacao = timezone.now()
            exame.save()

        return Response({'status': 'Notas liberadas com sucesso'})

    def calcular_nota_aluno(self, aluno, exame):
        respostas = Resposta.objects.filter(aluno=aluno, questao__exame=exame)
        return sum(resposta.calcular_pontuacao() for resposta in respostas)

    def calcular_nota_equipe(self, equipe, exame):
        respostas = Resposta.objects.filter(equipe=equipe, questao__exame=exame)
        return sum(resposta.calcular_pontuacao() for resposta in respostas)


class RespostaViewSet(viewsets.ModelViewSet):
    serializer_class = RespostaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        exame_id = self.kwargs.get('exame_pk')

        if user.tipo == Usuario.Tipo.ALUNO:
            return Resposta.objects.filter(aluno__usuario=user, questao__exame_id=exame_id)
        elif user.tipo == Usuario.Tipo.PROFESSOR:
            return Resposta.objects.filter(questao__exame_id=exame_id)
        return Resposta.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        questao = serializer.validated_data['questao']
        exame = questao.exame

        if exame.tipo == 'TBL' and exame.fase_tbl == 'gRAT':
            aluno = user.aluno
            equipe = aluno.equipes.filter(turma=exame.turma).first()
            if not equipe:
                raise serializers.ValidationError('Aluno não está em uma equipe')
            serializer.save(equipe=equipe)
        else:
            serializer.save(aluno=user.aluno)


class CorrecaoViewSet(viewsets.ModelViewSet):
    serializer_class = CorrecaoRespostaSerializer
    permission_classes = [IsAuthenticated]
    queryset = Resposta.objects.filter(questao__tipo='SUB', corrigida=False)

    def get_queryset(self):
        user = self.request.user
        if user.tipo == Usuario.Tipo.PROFESSOR:
            return self.queryset.filter(questao__exame__professor__usuario=user)
        return Resposta.objects.none()

    def perform_update(self, serializer):
        serializer.save(corrigida=True)


class NotaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo == Usuario.Tipo.ALUNO:
            return NotaAvaliacao.objects.filter(aluno__usuario=user)
        elif user.tipo == Usuario.Tipo.PROFESSOR:
            return NotaAvaliacao.objects.filter(exame__professor__usuario=user)
        return NotaAvaliacao.objects.none()


class NotaCompostaViewSet(viewsets.ModelViewSet):
    serializer_class = NotaCompostaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo == Usuario.Tipo.PROFESSOR:
            return NotaComposta.objects.filter(turma__professor_responsavel__usuario=user)
        return NotaComposta.objects.none()

    def create(self, request, *args, **kwargs):
        componentes = request.data.pop('componentes', [])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            nota_composta = serializer.save()

            for componente in componentes:
                comp_serializer = ComponenteNotaCompostaSerializer(data=componente)
                comp_serializer.is_valid(raise_exception=True)
                comp_serializer.save(nota_composta=nota_composta)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def calcular(self, request, pk=None):
        nota_composta = self.get_object()
        turma = nota_composta.turma

        with transaction.atomic():
            for aluno in turma.alunos_matriculados.all():
                ResultadoNotaComposta.calcular_para_aluno(aluno, nota_composta)

        return Response({'status': 'Notas compostas calculadas'})


class ResultadoNotaCompostaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ResultadoNotaCompostaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo == Usuario.Tipo.ALUNO:
            return ResultadoNotaComposta.objects.filter(aluno__usuario=user)
        elif user.tipo == Usuario.Tipo.PROFESSOR:
            return ResultadoNotaComposta.objects.filter(
                nota_composta__turma__professor_responsavel__usuario=user
            )
        return ResultadoNotaComposta.objects.none()
