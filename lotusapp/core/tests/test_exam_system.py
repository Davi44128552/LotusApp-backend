# tests/test_exam_system.py
from core.models import Alternativa, Aluno, Exame, Professor, Questao, Resposta, Turma, Usuario
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


class ExamSystemTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create professor
        prof_user = Usuario.objects.create_user(
            username='exam_prof',
            email='exam_prof@test.com',
            password='prof123',
            first_name='Exam',
            last_name='Professor',
            tipo=Usuario.Tipo.PROFESSOR,
        )
        self.professor = Professor.objects.create(usuario=prof_user)

        # Create student
        student_user = Usuario.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='student123',
            first_name='Test',
            last_name='Student',
            tipo=Usuario.Tipo.ALUNO,
        )
        self.student = Aluno.objects.create(usuario=student_user, semestre='2023.1')

        # Create turma
        self.turma = Turma.objects.create(
            disciplina='Exam Testing',
            semestre='2023.1',
            capacidade_maxima=30,
            quantidade_alunos=1,
            professor_responsavel=self.professor,
        )
        self.turma.alunos_matriculados.add(self.student)

        # Create exam
        self.exam = Exame.objects.create(
            turma=self.turma,
            tipo='TBL',
            fase='IRAT',
            titulo='Test Exam',
            deadline=timezone.now() + timezone.timedelta(days=1),
            professor=self.professor,
        )

        # Create question
        self.question = Questao.objects.create(
            exame=self.exam, enunciado='Test question?', tipo='ME', valor_total=10.0
        )

        # Create alternatives
        self.alt1 = Alternativa.objects.create(
            questao=self.question, texto='Correct answer', correta=True
        )
        self.alt2 = Alternativa.objects.create(
            questao=self.question, texto='Wrong answer', correta=False
        )

        # Student client
        self.student_client = APIClient()
        self.student_client.force_authenticate(user=student_user)

    def test_answer_submission(self):
        url = reverse('resposta-list', args=[self.turma.id, self.exam.id])
        data = {'questao': self.question.id, 'alternativa': self.alt1.id}
        response = self.student_client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Resposta.objects.count(), 1)

    def test_grade_release(self):
        # Submit answer first
        self.test_answer_submission()

        # Switch to professor client
        prof_client = APIClient()
        prof_client.force_authenticate(user=self.professor.usuario)

        # Release grades
        url = reverse('exame-liberar-notas', args=[self.exam.id])
        response = prof_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.exam.refresh_from_db()
        self.assertIsNotNone(self.exam.data_liberacao)

        # Verify grade calculation
        from core.models import NotaAvaliacao

        self.assertTrue(NotaAvaliacao.objects.filter(aluno=self.student, exame=self.exam).exists())
