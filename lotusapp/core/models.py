from django.contrib.auth.models import (  # Classe de usuário abstrata do Django
    AbstractUser,
    BaseUserManager,
)
from django.core.exceptions import ValidationError
from django.db import models, transaction
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
    TIPO_EXAME = [('TBL', 'TBL'), ('PBL', 'PBL')]
    FASE_TBL = [('IRAT', 'iRAT'), ('GRAT', 'gRAT')]

    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='exames')
    tipo = models.CharField(max_length=3, choices=TIPO_EXAME)
    fase = models.CharField(max_length=4, choices=FASE_TBL, null=True, blank=True)
    titulo = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    deadline = models.DateTimeField()
    data_liberacao = models.DateTimeField(null=True, blank=True)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    fase_associada = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    fator_penalidade = models.FloatField(default=0.5, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(fator_penalidade__gte=0) & models.Q(fator_penalidade__lte=1),
                name='fator_penalidade_range',
            )
        ]

    def clean(self):
        if self.tipo == 'TBL' and self.fase == 'GRAT' and not self.fase_associada:
            raise ValidationError('gRAT deve ter uma fase iRAT associada')

        if self.fase_associada and self.fase_associada.tipo != 'TBL':
            raise ValidationError('Fase associada deve ser um exame TBL')

        if self.fator_penalidade and (self.fator_penalidade < 0 or self.fator_penalidade > 1):
            raise ValidationError('Fator de penalidade deve estar entre 0 e 1')

    @property
    def aberto(self):
        return timezone.now() < self.deadline

    @property
    def estado(self):
        if self.aberto:
            return 'ABERTO'
        if self.data_liberacao:
            return 'NOTAS_LIBERADAS'
        return 'AGUARDANDO_CORRECAO'

    def liberar_notas(self):
        if self.data_liberacao:
            return False

        if self.tipo == 'PBL':
            if Resposta.objects.filter(
                questao__exame=self, questao__tipo='SUB', corrigida=False
            ).exists():
                return False

        # Calcular notas antes de liberar
        NotaAvaliacao.objects.calcular_para_exame(self)

        # Aplicar penalidades para gRAT
        if self.tipo == 'TBL' and self.fase == 'GRAT':
            from .services import AvaliacaoService

            AvaliacaoService.aplicar_penalidade_grat(self)

        self.data_liberacao = timezone.now()
        self.save()

        # Recalcular notas compostas
        for comp in ComponenteNotaComposta.objects.filter(exame=self):
            comp.nota_composta.calcular_para_todos()

        return True


class Questao(models.Model):
    TIPO_QUESTAO = [('ME', 'Múltipla Escolha'), ('VF', 'Verdadeiro/Falso'), ('SUB', 'Subjetiva')]

    exame = models.ForeignKey(Exame, on_delete=models.CASCADE, related_name='questoes')
    enunciado = models.TextField()
    tipo = models.CharField(max_length=3, choices=TIPO_QUESTAO)
    valor_total = models.DecimalField(max_digits=5, decimal_places=2)
    resposta_modelo = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.tipo in ['ME', 'VF'] and not self.alternativas.exists():
            self.criar_alternativas_padrao()

    def criar_alternativas_padrao(self):
        for i in range(4):
            Alternativa.objects.create(questao=self, texto=f'Alternativa {i + 1}', correta=(i == 0))


class Alternativa(models.Model):
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='alternativas')
    texto = models.CharField(max_length=500)
    correta = models.BooleanField(default=False)
    pontuacao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Pontuação individual (deixe em branco para distribuição automática)',
    )

    def calcular_pontuacao(self):
        if self.pontuacao is not None:
            return self.pontuacao

        # Distribuição automática
        total_corretas = self.questao.alternativas.filter(correta=True).count()
        if total_corretas > 0:
            return self.questao.valor_total / total_corretas
        return 0


class Resposta(models.Model):
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='respostas')
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, null=True, blank=True)
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, null=True, blank=True)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.SET_NULL, null=True, blank=True)
    resposta_texto = models.TextField(null=True, blank=True)
    data_resposta = models.DateTimeField(auto_now_add=True)
    corrigida = models.BooleanField(default=False)
    pontuacao_obtida = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comentario_correcao = models.TextField(null=True, blank=True)

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


class NotaAvaliacaoManager(models.Manager):
    def calcular_para_exame(self, exame):
        with transaction.atomic():
            # Para TBL
            if exame.tipo == 'TBL':
                if exame.fase == 'IRAT':
                    for aluno in exame.turma.alunos_matriculados.all():
                        nota = self._calcular_nota_aluno(aluno, exame)
                        self.update_or_create(
                            aluno=aluno, exame=exame, defaults={'valor': nota, 'tipo': 'iRAT'}
                        )
                elif exame.fase == 'GRAT':
                    for equipe in exame.turma.equipes.all():
                        nota = self._calcular_nota_equipe(equipe, exame)
                        self.update_or_create(
                            equipe=equipe, exame=exame, defaults={'valor': nota, 'tipo': 'gRAT'}
                        )
            # Para PBL
            else:
                for aluno in exame.turma.alunos_matriculados.all():
                    nota = self._calcular_nota_aluno(aluno, exame)
                    self.update_or_create(
                        aluno=aluno, exame=exame, defaults={'valor': nota, 'tipo': 'PBL'}
                    )

    def _calcular_nota_aluno(self, aluno, exame):
        return sum(
            resposta.calcular_pontuacao()
            for resposta in Resposta.objects.filter(aluno=aluno, questao__exame=exame)
        )

    def _calcular_nota_equipe(self, equipe, exame):
        return sum(
            resposta.calcular_pontuacao()
            for resposta in Resposta.objects.filter(equipe=equipe, questao__exame=exame)
        )

    @staticmethod
    def aplicar_penalidade_grat(nota_grat, media_irat, fator_penalidade):
        """Aplica penalidade conforme especificação"""
        if media_irat <= 0 or nota_grat >= media_irat:
            return nota_grat

        diferenca = media_irat - nota_grat
        # Verificar se a diferença é mais que 10% da média
        if diferenca <= 0.1 * media_irat:
            return nota_grat

        penalidade = diferenca / media_irat
        fator_ajuste = min(1.0, fator_penalidade * penalidade)
        return nota_grat * (1 - fator_ajuste)


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

    objects = NotaAvaliacaoManager()


class NotaCompostaManager(models.Manager):
    def calcular_para_turma(self, turma):
        for nota_composta in self.filter(turma=turma):
            nota_composta.calcular_para_todos()


class NotaComposta(models.Model):
    nome = models.CharField(max_length=100)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

    objects = NotaCompostaManager()

    def calcular_para_todos(self):
        for aluno in self.turma.alunos_matriculados.all():
            ResultadoNotaComposta.calcular_para_aluno(aluno, self)


class ComponenteNotaComposta(models.Model):
    nota_composta = models.ForeignKey(
        NotaComposta, on_delete=models.CASCADE, related_name='componentes'
    )
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE)
    peso = models.DecimalField(max_digits=5, decimal_places=2)

    def clean(self):
        if self.peso <= 0:
            raise ValidationError('Peso deve ser maior que zero')

        # Validar soma dos pesos
        soma_pesos = (
            ComponenteNotaComposta.objects.filter(nota_composta=self.nota_composta)
            .exclude(id=self.id)
            .aggregate(total=models.Sum('peso'))['total']
            or 0
        )

        if soma_pesos + self.peso > 2.0:  # Permitir até 200%
            raise ValidationError('Soma dos pesos não pode exceder 2.0 (200%)')


class ResultadoNotaComposta(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    nota_composta = models.ForeignKey(NotaComposta, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    data_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['aluno', 'nota_composta']]

    @classmethod
    def calcular_para_aluno(cls, aluno, nota_composta):
        total = 0
        for componente in nota_composta.componentes.select_related('exame'):
            exame = componente.exame

            try:
                if exame.tipo == 'TBL' and exame.fase == 'GRAT':
                    equipe = aluno.equipes.get(turma=nota_composta.turma)
                    nota_grat = NotaAvaliacao.objects.get(
                        equipe=equipe, exame=exame, tipo='gRAT'
                    ).valor

                    # Calcular média iRAT da equipe
                    media_irat = (
                        NotaAvaliacao.objects.filter(
                            aluno__in=equipe.alunos.all(), exame=exame.fase_associada, tipo='iRAT'
                        ).aggregate(media=Avg('valor'))['media']
                        or 0
                    )

                    # Aplicar penalidade
                    valor_nota = NotaAvaliacao.aplicar_penalidade_grat(
                        nota_grat, media_irat, exame.fator_penalidade or 0.5
                    )
                else:
                    nota = NotaAvaliacao.objects.get(aluno=aluno, exame=exame)
                    valor_nota = nota.valor
            except (Equipe.DoesNotExist, NotaAvaliacao.DoesNotExist):
                valor_nota = 0

            total += valor_nota * componente.peso

        # Truncar em 100 e garantir não negativo
        valor_final = max(0, min(total, 100))
        obj, created = cls.objects.update_or_create(
            aluno=aluno,
            nota_composta=nota_composta,
            defaults={'valor': valor_final, 'data_calculo': timezone.now()},
        )
        return obj
