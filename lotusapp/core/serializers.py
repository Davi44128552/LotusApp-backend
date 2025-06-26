from django.utils import timezone
from rest_framework import serializers

from .models import (
    Alternativa,
    ComponenteNotaComposta,
    Exame,
    NotaAvaliacao,
    NotaComposta,
    Questao,
    Resposta,
    ResultadoNotaComposta,
)


class AlternativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternativa
        fields = ['id', 'texto', 'correta', 'pontuacao']


class QuestaoSerializer(serializers.ModelSerializer):
    alternativas = AlternativaSerializer(many=True, read_only=True)

    class Meta:
        model = Questao
        fields = ['id', 'enunciado', 'tipo', 'valor_total', 'alternativas']


class ExameSerializer(serializers.ModelSerializer):
    questoes = QuestaoSerializer(many=True, read_only=True)
    fase_tbl = serializers.SerializerMethodField()
    professor = serializers.StringRelatedField()
    aberto = serializers.BooleanField(read_only=True)

    class Meta:
        model = Exame
        fields = '__all__'

    def get_fase_tbl(self, obj):
        return obj.fase_tbl


class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = '__all__'
        read_only_fields = ('data_resposta', 'corrigida', 'pontuacao_obtida')

    def validate(self, data):
        questao = data['questao']
        exame = questao.exame

        if timezone.now() > exame.deadline:
            raise serializers.ValidationError('Prazo expirado para este exame')

        if exame.tipo == 'TBL' and exame.fase_tbl == 'gRAT' and not data.get('equipe'):
            raise serializers.ValidationError('Respostas gRAT devem ser por equipe')

        return data


class CorrecaoRespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = ['id', 'pontuacao_obtida', 'corrigida']

    def validate_pontuacao_obtida(self, value):
        questao = self.instance.questao
        if value < 0 or value > questao.valor_total:
            raise serializers.ValidationError(
                f'Pontuação deve estar entre 0 e {questao.valor_total}'
            )
        return value


class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaAvaliacao
        fields = '__all__'

class ComponenteNotaCompostaSerializer(serializers.ModelSerializer):
    exame_info = ExameSerializer(source='exame', read_only=True)

    class Meta:
        model = ComponenteNotaComposta
        fields = '__all__'


class NotaCompostaSerializer(serializers.ModelSerializer):
    componentes = ComponenteNotaCompostaSerializer(many=True, read_only=True)

    class Meta:
        model = NotaComposta
        fields = '__all__'

    def validate(self, data):
        componentes = self.context.get('componentes', [])
        total_pesos = sum(comp['peso'] for comp in componentes)

        if total_pesos < 1:
            raise serializers.ValidationError('Soma dos pesos deve ser >= 1')

        return data


class ResultadoNotaCompostaSerializer(serializers.ModelSerializer):
    aluno_info = serializers.StringRelatedField(source='aluno')
    nota_composta_info = serializers.StringRelatedField(source='nota_composta')

    class Meta:
        model = ResultadoNotaComposta
        fields = '__all__'
