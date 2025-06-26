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

admin.site.register(Usuario)
admin.site.register(Professor)
admin.site.register(Aluno)
admin.site.register(CasoClinico)
admin.site.register(Diagnostico)
admin.site.register(Turma)
admin.site.register(Equipe)
admin.site.register(TentativaDiagnostico)
admin.site.register(Exame)
admin.site.register(Questao)
admin.site.register(Alternativa)
admin.site.register(Resposta)
admin.site.register(NotaAvaliacao)
admin.site.register(NotaComposta)
admin.site.register(ComponenteNotaComposta)
admin.site.register(ResultadoNotaComposta)
