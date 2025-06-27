from django.db.models import Avg

from .models import ComponenteNotaComposta, NotaAvaliacao, ResultadoNotaComposta


class AvaliacaoService:
    @staticmethod
    def aplicar_penalidade_grat(exame_grat):
        """
        Aplica penalidade a todas as notas gRAT de um exame
        """
        if not exame_grat.fase_associada:
            return

        for nota_grat in NotaAvaliacao.objects.filter(exame=exame_grat, tipo='gRAT'):
            equipe = nota_grat.equipe

            # Calcular média iRAT da equipe
            media_irat = (
                NotaAvaliacao.objects.filter(
                    aluno__in=equipe.alunos.all(), exame=exame_grat.fase_associada, tipo='iRAT'
                ).aggregate(media=Avg('valor'))['media']
                or 0
            )

            # Aplicar penalidade
            nova_nota = NotaAvaliacao.aplicar_penalidade_grat(
                nota_grat.valor, media_irat, exame_grat.fator_penalidade or 0.5
            )

            nota_grat.valor = nova_nota
            nota_grat.save()

            # Atualizar notas compostas para cada aluno da equipe
            for aluno in equipe.alunos.all():
                for componente in ComponenteNotaComposta.objects.filter(exame=exame_grat):
                    ResultadoNotaComposta.calcular_para_aluno(aluno, componente.nota_composta)

    @staticmethod
    def calcular_notas_compostas_apos_exame(exame):
        """
        Recalcula todas as notas compostas que incluem este exame
        """
        for componente in ComponenteNotaComposta.objects.filter(exame=exame):
            componente.nota_composta.calcular_para_todos()
