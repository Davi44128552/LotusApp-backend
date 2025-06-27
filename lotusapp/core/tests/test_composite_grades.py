# tests/test_composite_grades.py
from core.models import (
    Aluno,
    ComponenteNotaComposta,
    Exame,
    NotaAvaliacao,
    NotaComposta,
    Professor,
    Turma,
    Usuario,
)
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


class CompositeGradeTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create professor
        prof_user = Usuario.objects.create_user(
            username='grade_prof',
            email='grade_prof@test.com',
            password='prof123',
            first_name='Grade',
            last_name='Professor',
            tipo=Usuario.Tipo.PROFESSOR,
        )
        self.professor = Professor.objects.create(usuario=prof_user)

        # Create student
        student_user = Usuario.objects.create_user(
            username='comp_student',
            email='comp_student@test.com',
            password='student123',
            first_name='Composite',
            last_name='Student',
            tipo=Usuario.Tipo.ALUNO,
        )
        self.student = Aluno.objects.create(usuario=student_user, semestre='2023.1')

        # Create turma
        self.turma = Turma.objects.create(
            disciplina='Composite Testing',
            semestre='2023.1',
            capacidade_maxima=30,
            quantidade_alunos=1,
            professor_responsavel=self.professor,
        )
        self.turma.alunos_matriculados.add(self.student)

        # Create exam
        self.exam = Exame.objects.create(
            turma=self.turma,
            tipo='PBL',
            titulo='Component Exam',
            deadline=timezone.now() - timezone.timedelta(days=1),  # Past deadline
            professor=self.professor,
        )

        # Create composite grade
        self.composta = NotaComposta.objects.create(nome='Final Grade', turma=self.turma)

        # Add component
        self.component = ComponenteNotaComposta.objects.create(
            nota_composta=self.composta, exame=self.exam, peso=1.0
        )

        # Authenticate as professor
        self.client.force_authenticate(user=prof_user)

    def test_composite_calculation(self):
        # Create a grade for the exam
        NotaAvaliacao.objects.create(aluno=self.student, exame=self.exam, tipo='PBL', valor=85.0)

        # Trigger calculation
        url = reverse('notacomp-calcular', args=[self.composta.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        # Verify results
        from core.models import ResultadoNotaComposta

        result = ResultadoNotaComposta.objects.get(nota_composta=self.composta, aluno=self.student)
        self.assertEqual(result.valor, 85.0)
