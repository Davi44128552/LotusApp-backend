from django.db import models
from django.db.models import JSONField
from django.contrib.auth.models import AbstractUser, BaseUserManager # Classe de usuário abstrata do Django

class UsuarioManager(BaseUserManager):
    def create_user(self,username , email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email deve ser fornecido')
        if not username:
            raise ValueError('O nome de usuário deve ser fornecido')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo', Usuario.Tipo.ADMINISTRADOR)

        if 'first_name' not in extra_fields:
            raise ValueError('O primeiro nome deve ser fornecido para o superusuário')
        
        return self.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )
    
# Criando as classes das entidades
# Classe usuário
class Usuario(AbstractUser):
    class Tipo(models.TextChoices):
        PROFESSOR = 'prof', 'Professor'
        ALUNO = 'alu', 'Aluno'
        ADMINISTRADOR = 'admin', 'Administrador'

    # Campos django: username, first_name, last_name, email, password, data_joined, is_active, is_staff, is_superuser
    cpf = models.CharField(
        max_length = 11, 
        unique = True,
        null = True,
        blank = True
    )
    # Não é unique por padrão
    email = models.EmailField(
        unique = True
    )
    foto_url = models.CharField(max_length = 100)
    tipo = models.CharField(
        max_length = 5,
        choices = Tipo.choices,
        default= Tipo.ALUNO
    )
    USERNAME_FIELD = 'email'
    # Requeridos ao criar um superusuário
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    objects = UsuarioManager()




# Classe professor
class Professor(models.Model):
    # Cria uma relação de perfil entre o usuário e o professor
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        related_name='professor'
    )
    formacao = models.CharField(max_length = 100)
    especialidade = models.CharField(max_length = 100)

    def save(self, *args, **kwargs):
        self.usuario.tipo = Usuario.Tipo.PROFESSOR
        # Salvando as alterações no usuário associado
        self.usuario.save()
        super().save(*args, **kwargs)

# Classe aluno
class Aluno(models.Model):
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        related_name='aluno'
    )
    semestre = models.CharField(max_length = 6)
    ira = models.DecimalField(
        max_digits = 4, 
        decimal_places = 3
        )

    def save(self, *args, **kwargs):
        self.usuario.tipo = Usuario.Tipo.ALUNO
        self.usuario.save()
        super().save(*args, **kwargs)

# Classe de caso clínico
class CasoClinico(models.Model):
    titulo = models.CharField(max_length = 100)
    descricao = models.CharField(max_length = 1000)
    area = models.CharField(max_length = 100)
    arquivos = JSONField(default = list)
    professor_responsavel = models.ForeignKey(
        Professor,
        on_delete = models.CASCADE, # TODO: pensar se é deletado em cascata ou SET_NULL
        null = True,
        blank = True,
        related_name='casos_clinicos_criados_pelo_professor'
    )
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
    alunos_matriculados = models.ManyToManyField(
        Aluno,
        blank = True,
        related_name='turmas_matriculadas'
    )

# Classe da equipe
class Equipe(models.Model):
    nome = models.CharField(max_length = 100)
    turma = models.ForeignKey(
        Turma,
        on_delete = models.CASCADE,
        related_name='equipes'
    )
    alunos = models.ManyToManyField(
        Aluno,
        blank = True,
        related_name='equipes'
    )
    caso_designado = models.ForeignKey(
        CasoClinico,
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name='equipes_designadas'
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