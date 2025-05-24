from django.db import models
from django.db.models import JSONField

# Criando as classes das entidades
# Classe usuário
class Usuario(models.Model):
    nome = models.CharField(max_length = 100)
    cpf = models.CharField(
        max_length = 11, 
        unique = True
        )
    email = models.CharField(max_length = 200)
    senha = models.CharField(max_length = 100)
    foto_url = models.CharField(max_length = 100)
    data_cadastro = models.DateField()

    class Tipo(models.TextChoices):
        PROFESSOR = 'prof', 'Professor'
        ALUNO = 'alu', 'Aluno'
        ADMINISTRADOR = 'admin', 'Administrador'

    tipo = models.CharField(
        max_length = 5,
        choices = Tipo.choices,
    )

# Classe professor
class Professor(Usuario):
    formacao = models.CharField(max_length = 100)
    especialidade = models.CharField(max_length = 100)

    def save(self, *args, **kwargs):
        self.tipo = Usuario.Tipo.PROFESSOR
        super().save(*args, **kwargs)

# Classe aluno
class Aluno(Usuario):
    semestre = models.CharField(max_length = 6)
    ira = models.DecimalField(
        max_digits = 4, 
        decimal_places = 3
        )

    def save(self, *args, **kwargs):
        self.tipo = Usuario.Tipo.ALUNO
        super().save(*args, **kwargs)

# Classe de caso clínico
class CasoClinico(models.Model):
    titulo = models.CharField(max_length = 100)
    descricao = models.CharField(max_length = 1000)
    area = models.CharField(max_length = 100)
    arquivos = JSONField(default = list)

    class Dificuldade(models.TextChoices):
        INICIANTE = 'F', 'Iniciante'
        INTERMEDIARIO = 'M', 'Intermediário'
        AVANÇADO = 'D', 'Avançado'

    dificuldade = models.CharField(
        max_length = 1,
        choices = Dificuldade.choices,
        default = Dificuldade.INTERMEDIARIO
    )

# Classe de Diagnóstico
class Diagnostico(models.Model):
    descricao = models.CharField(max_length = 1000)
    caso_clinico = models.ForeignKey(
        CasoClinico,
        on_delete = models.CASCADE
    )
    resposta_professor = models.ForeignKey(
        Professor,
        on_delete = models.CASCADE
    )

# Classe da turma
class Turma(models.Model):
    disciplina = models.CharField(max_length = 100)
    semestre = models.CharField(max_length = 6)
    capacidade_maxima = models.SmallIntegerField()
    quantidade_alunos = models.SmallIntegerField()
    professor_responsavel = models.ForeignKey(
        Professor,
        on_delete = models.SET_NULL,
        null = True,
        blank = True
        )

# Classe da equipe
class Equipe(models.Model):
    nome = models.CharField(max_length = 100)
    turma = models.ForeignKey(
        Turma,
        on_delete = models.CASCADE
    )

# Classe de Diagnóstico das equipes de alunos
class TentativaDiagnostico(models.Model):
    descricao = models.CharField(max_length = 1000)
    caso_clinico = models.ForeignKey(
        CasoClinico,
        on_delete = models.CASCADE
    )
    equipe = models.ForeignKey(
        Equipe,
        on_delete = models.CASCADE
    )