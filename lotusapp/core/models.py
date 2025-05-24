from django.db import models
from django.contrib.postgres.fields import JSONField

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

    class tipo(models.TextChoices):
        PROFESSOR = 'prof', 'Professor'
        ALUNO = 'alu', 'Aluno'
        ADMINISTRADOR = 'admin', 'Administrador'

# Classe professor
class Professor(models.Model):
    formacao = models.CharField(max_length = 100)
    especialidade = models.CharField(max_length = 100)

# Classe aluno
class Aluno(models.Model):
    semestre = models.CharField(max_length = 6)
    ira = models.DecimalField(
        max_digits = 4, 
        decimal_places = 3
        )

# Classe de caso clínico
class CasoClinico(models.Model):
    titulo = models.CharField(max_length = 100)
    descricao = models.CharField(max_length = 1000)
    area = models.CharField(max_length = 100)
    arquivos = JSONField(default = list)

    class dificuldade(models.TextChoices):
        INICIANTE = 'Iniciante'
        INTERMEDIARIO = 'Intermediário'
        AVANÇADO = 'Avançado'

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

# Classe Equipe
class Turma(models.Model):
    disciplina = models.CharField(max_length = 100)
    semestre = models.CharField(max_length = 6)
    capacidade_maxima = models.SmallIntegerField()
    quantidade_alunos = models.SmallIntegerField()
    professor_responsavel = models.ForeignKey(Professor)