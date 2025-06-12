from django.contrib import admin

from .models import (
    Aluno,
    CasoClinico,
    Diagnostico,
    Equipe,
    Professor,
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
