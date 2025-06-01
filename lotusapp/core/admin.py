from django.contrib import admin
from .models import (
    Usuario,
    Professor,
    Aluno,
    CasoClinico,
    Diagnostico,
    Turma,
    Equipe,
    TentativaDiagnostico
)

admin.site.register(Usuario)
admin.site.register(Professor)
admin.site.register(Aluno)
admin.site.register(CasoClinico)
admin.site.register(Diagnostico)
admin.site.register(Turma)
admin.site.register(Equipe)
admin.site.register(TentativaDiagnostico)
