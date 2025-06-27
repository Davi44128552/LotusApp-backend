from django.contrib import admin

from .models import (
    Alternativa,
    Aluno,
    CasoClinico,
    ComponenteNotaComposta,
    Diagnostico,
    Equipe,
    Exame,
    NotaAvaliacao,
    NotaComposta,
    Professor,
    Questao,
    Resposta,
    ResultadoNotaComposta,
    TentativaDiagnostico,
    Turma,
    Usuario,
)


@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fase', 'turma', 'deadline', 'estado')
    list_filter = ('tipo', 'fase', 'turma')
    search_fields = ('titulo', 'descricao')
    readonly_fields = ('estado',)


@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    list_display = ('enunciado', 'tipo', 'valor_total', 'exame')
    list_filter = ('tipo', 'exame')
    search_fields = ('enunciado',)


@admin.register(Resposta)
class RespostaAdmin(admin.ModelAdmin):
    list_display = ('questao', 'aluno', 'equipe', 'data_resposta', 'corrigida')
    list_filter = ('questao__exame', 'corrigida')
    search_fields = ('questao__enunciado', 'aluno__usuario__first_name')


@admin.register(NotaAvaliacao)
class NotaAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('exame', 'tipo', 'aluno', 'equipe', 'valor')
    list_filter = ('tipo', 'exame')
    search_fields = ('aluno__usuario__first_name', 'equipe__nome')


@admin.register(NotaComposta)
class NotaCompostaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'turma')
    search_fields = ('nome', 'turma__disciplina')


@admin.register(ResultadoNotaComposta)
class ResultadoNotaCompostaAdmin(admin.ModelAdmin):
    list_display = ('nota_composta', 'aluno', 'valor')
    list_filter = ('nota_composta',)
    search_fields = ('aluno__usuario__first_name',)


admin.site.register(Usuario)
admin.site.register(Professor)
admin.site.register(Aluno)
admin.site.register(CasoClinico)
admin.site.register(Diagnostico)
admin.site.register(Turma)
admin.site.register(Equipe)
admin.site.register(TentativaDiagnostico)
admin.site.register(Alternativa)
admin.site.register(ComponenteNotaComposta)
