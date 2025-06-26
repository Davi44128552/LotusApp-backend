from django.contrib.auth.models import (  # Classe de usuário abstrata do Django
    AbstractUser,
    BaseUserManager,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, JSONField
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email deve ser fornecido')
        if not username:
            raise ValueError('O nome de usuário deve ser fornecido')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo', Usuario.Tipo.ADMINISTRADOR)

        if 'first_name' not in extra_fields:
            raise ValueError('O primeiro nome deve ser fornecido para o superusuário')

        return self.create_user(username=username, email=email, password=password, **extra_fields)


# Criando as classes das entidades
# Classe usuário
class Usuario(AbstractUser):
    class Tipo(models.TextChoices):
        PROFESSOR = 'prof', 'Professor'
        ALUNO = 'alu', 'Aluno'
        ADMINISTRADOR = 'admin', 'Administrador'

    # Campos django: username, first_name, last_name, email, password, data_joined, is_active
    # is_staff, is_superuser
    cpf = models.CharField(max_length=11, unique=True, null=True, blank=True)
    # Não é unique por padrão
    email = models.EmailField(unique=True)
    foto_url = models.CharField(max_length=100)
    tipo = models.CharField(max_length=5, choices=Tipo.choices, default=Tipo.ALUNO)
    USERNAME_FIELD = 'email'
    # Requeridos ao criar um superusuário
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    objects = UsuarioManager()


# Classe professor
class Professor(models.Model):
    # Cria uma relação de perfil entre o usuário e o professor
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, primary_key=True, related_name='professor'
    )
    formacao = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.usuario.tipo = Usuario.Tipo.PROFESSOR
        # Salvando as alterações no usuário associado
        self.usuario.save()
        super().save(*args, **kwargs)


# Classe aluno
class Aluno(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, primary_key=True, related_name='aluno'
    )
    semestre = models.CharField(max_length=6)
    matricula = models.CharField(max_length=10, unique=True)

    def save(self, *args, **kwargs):
        self.usuario.tipo = Usuario.Tipo.ALUNO
        self.usuario.save()
        super().save(*args, **kwargs)


# Classe de caso clínico
class CasoClinico(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.CharField(max_length=1000)
    area = models.CharField(max_length=100)
    arquivos = JSONField(default=list)
    professor_responsavel = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,  # TODO: pensar se é deletado em cascata ou SET_NULL
        null=True,
        blank=True,
        related_name='casos_clinicos_criados_pelo_professor',
    )

    class Dificuldade(models.TextChoices):
        INICIANTE = 'F', 'Iniciante'
        INTERMEDIARIO = 'M', 'Intermediário'
        AVANÇADO = 'D', 'Avançado'

    dificuldade = models.CharField(
        max_length=1, choices=Dificuldade.choices, default=Dificuldade.INTERMEDIARIO
    )


# Classe de Diagnóstico
class Diagnostico(models.Model):
    descricao = models.CharField(max_length=1000)
    caso_clinico = models.ForeignKey(CasoClinico, on_delete=models.CASCADE)
    resposta_professor = models.ForeignKey(Professor, on_delete=models.CASCADE)


# Classe da turma
class Turma(models.Model):
    disciplina = models.CharField(max_length=100)
    semestre = models.CharField(max_length=6)
    capacidade_maxima = models.SmallIntegerField()
    quantidade_alunos = models.SmallIntegerField()
    professor_responsavel = models.ForeignKey(
        Professor, on_delete=models.SET_NULL, null=True, blank=True
    )
    alunos_matriculados = models.ManyToManyField(
        Aluno, blank=True, related_name='turmas_matriculadas'
    )


# Classe da equipe
class Equipe(models.Model):
    nome = models.CharField(max_length=100)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='equipes')
    alunos = models.ManyToManyField(Aluno, blank=True, related_name='equipes')
    caso_designado = models.ForeignKey(
        CasoClinico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_designadas',
    )


# Classe de Diagnóstico das equipes de alunos
class TentativaDiagnostico(models.Model):
    descricao = models.CharField(max_length=1000)
    caso_clinico = models.ForeignKey(CasoClinico, on_delete=models.CASCADE)
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE)


# Classe de notas
class Notas(models.Model):
    valor = models.DecimalField(max_digits=3, decimal_places=1)

    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE)


# ======================================
# Modelos para sistema de avaliação TBL/PBL
# ======================================


class Exame(models.Model):
    class TipoExame(models.TextChoices):
        TBL = 'TBL', 'TBL'
        PBL = 'PBL', 'PBL'

    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='exames_avaliacao')
    tipo = models.CharField(max_length=3, choices=TipoExame.choices)
    titulo = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    deadline = models.DateTimeField()
    data_liberacao = models.DateTimeField(null=True, blank=True)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    fase_associada = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def aberto(self):
        return timezone.now() < self.deadline

    @property
    def fase_tbl(self):
        if self.tipo == 'TBL':
            return 'iRAT' if not self.fase_associada else 'gRAT'
        return None

    def liberar_notas(self):
        if self.tipo == 'PBL':
            if Resposta.objects.filter(
                questao__exame=self, questao__tipo='SUB', corrigida=False
            ).exists():
                return False
        self.data_liberacao = timezone.now()
        self.save()
        return True


class Questao(models.Model):
    TIPO_QUESTAO = [('ME', 'Múltipla Escolha'), ('VF', 'Verdadeiro/Falso'), ('SUB', 'Subjetiva')]

    exame = models.ForeignKey(Exame, on_delete=models.CASCADE, related_name='questoes')
    enunciado = models.TextField()
    tipo = models.CharField(max_length=3, choices=TIPO_QUESTAO)
    valor_total = models.DecimalField(max_digits=5, decimal_places=2)

    def criar_alternativas_padrao(self):
        if self.tipo in ['ME', 'VF'] and not self.alternativas.exists():
            for i in range(4):
                Alternativa.objects.create(
                    questao=self, texto=f'Alternativa {i + 1}', correta=(i == 0)
                )

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created:
            self.criar_alternativas_padrao()


class Alternativa(models.Model):
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='alternativas')
    texto = models.CharField(max_length=500)
    correta = models.BooleanField(default=False)
    pontuacao = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def calcular_pontuacao(self):
        if self.pontuacao is None:
            corretas = self.questao.alternativas.filter(correta=True).count()
            if corretas > 0:
                return self.questao.valor_total / corretas
            return 0
        return self.pontuacao


class Resposta(models.Model):
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='respostas')
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, null=True, blank=True)
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, null=True, blank=True)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.SET_NULL, null=True, blank=True)
    resposta_texto = models.TextField(null=True, blank=True)
    data_resposta = models.DateTimeField(auto_now_add=True)
    corrigida = models.BooleanField(default=False)
    pontuacao_obtida = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['questao', 'aluno'],
                name='resposta_unica_aluno',
                condition=models.Q(equipe__isnull=True),
            ),
            models.UniqueConstraint(
                fields=['questao', 'equipe'],
                name='resposta_unica_equipe',
                condition=models.Q(aluno__isnull=True),
            ),
        ]

    def clean(self):
        if not self.aluno and not self.equipe:
            raise ValidationError('Resposta deve estar associada a aluno ou equipe')

        if self.questao.tipo in ['ME', 'VF'] and not self.alternativa:
            raise ValidationError('Questões objetivas requerem alternativa selecionada')

        if self.questao.tipo == 'SUB' and not self.resposta_texto:
            raise ValidationError('Questões subjetivas requerem texto de resposta')

    def calcular_pontuacao(self):
        if self.questao.tipo == 'SUB' and self.corrigida:
            return self.pontuacao_obtida or 0

        if self.alternativa and self.alternativa.correta:
            return self.alternativa.calcular_pontuacao()

        return 0


class NotaAvaliacao(models.Model):
    TIPO_NOTA = [
        ('iRAT', 'Individual RAT'),
        ('gRAT', 'Grupal RAT'),
        ('PBL', 'Avaliação PBL'),
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, null=True, blank=True)
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, null=True, blank=True)
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=4, choices=TIPO_NOTA)
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    data_criacao = models.DateTimeField(auto_now_add=True)

    @classmethod
    def calcular_penalidade_grat(cls, equipe, exame_grat):
        exame_irat = exame_grat.fase_associada
        if not exame_irat:
            return exame_grat.valor

        notas_irat = NotaAvaliacao.objects.filter(
            aluno__in=equipe.alunos.all(), exame=exame_irat, tipo='iRAT'
        )
        media_irat = notas_irat.aggregate(media=Avg('valor'))['media'] or 0

        nota_grat = NotaAvaliacao.objects.get(equipe=equipe, exame=exame_grat, tipo='gRAT').valor

        diferenca = media_irat - nota_grat
        if media_irat > 0 and diferenca > 10:
            penalidade = min(1.0, diferenca / media_irat)
            return nota_grat * (1 - penalidade)
        return nota_grat


class NotaComposta(models.Model):
    nome = models.CharField(max_length=100)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)


class ComponenteNotaComposta(models.Model):
    nota_composta = models.ForeignKey(
        NotaComposta, on_delete=models.CASCADE, related_name='componentes'
    )
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE)
    peso = models.DecimalField(max_digits=5, decimal_places=2)

    def clean(self):
        if self.peso <= 0:
            raise ValidationError('Peso deve ser maior que zero')


class ResultadoNotaComposta(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    nota_composta = models.ForeignKey(NotaComposta, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=5, decimal_places=2)

    @classmethod
    def calcular_para_aluno(cls, aluno, nota_composta):
        total = 0
        for componente in nota_composta.componentes.all():
            nota = NotaAvaliacao.objects.filter(aluno=aluno, exame=componente.exame).first()

            if nota:
                if componente.exame.tipo == 'TBL' and componente.exame.fase_tbl == 'gRAT':
                    try:
                        equipe = aluno.equipes.get(turma=nota_composta.turma)
                        valor_nota = NotaAvaliacao.calcular_penalidade_grat(
                            equipe, componente.exame
                        )
                    except Equipe.DoesNotExist:
                        valor_nota = nota.valor
                else:
                    valor_nota = nota.valor

                total += valor_nota * componente.peso

        valor_final = min(total, 100)
        obj, created = cls.objects.update_or_create(
            aluno=aluno, 
            nota_composta=nota_composta, 
            defaults={'valor': valor_final}
        )
        return obj
