import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

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
    Turma,
)

User = get_user_model()


class UserAuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')

        self.prof_data = {
            'nome': 'Maria',
            'sobrenome': 'Silva',
            'cpf': '12345678901',
            'email': 'maria@example.com',
            'senha': 'StrongP@ss123',
            'username': 'maria_prof',
            'tipo': 'prof',
            'formacao': 'Doutorado em Medicina',
            'especialidade': 'Cardiologia',
        }

        self.aluno_data = {
            'nome': 'João',
            'sobrenome': 'Souza',
            'matricula': '20230001',
            'cpf': '09876543210',
            'email': 'joao@example.com',
            'senha': 'StudentP@ss123',
            'username': 'joao_student',
            'tipo': 'alu',
            'semestre': '2023.1',
        }

    def test_user_registration(self):
        # Test professor registration
        response = self.client.post(
            self.register_url, data=json.dumps(self.prof_data), content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Professor.objects.count(), 1)

        # Test student registration
        response = self.client.post(
            self.register_url, data=json.dumps(self.aluno_data), content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Aluno.objects.count(), 1)

        # Test duplicate email
        duplicate_data = self.prof_data.copy()
        duplicate_data['cpf'] = '11111111111'
        duplicate_data['username'] = 'new_username'
        response = self.client.post(
            self.register_url, data=json.dumps(duplicate_data), content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Este email já está cadastrado', response.data['erro'])

    def test_user_login(self):
        # Create user first
        self.client.post(
            self.register_url, data=json.dumps(self.aluno_data), content_type='application/json'
        )

        # Valid login
        response = self.client.post(
            self.login_url,
            data=json.dumps({'email': self.aluno_data['email'], 'senha': self.aluno_data['senha']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Login bem-sucedido', response.data['mensagem'])

        # Invalid credentials
        response = self.client.post(
            self.login_url,
            data=json.dumps({'email': self.aluno_data['email'], 'senha': 'wrongpassword'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response_data = response.json()
        self.assertIn('Login bem-sucedido', response_data['mensagem'])


class ProfessorViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='prof_test',
            email='prof@example.com',
            password='testpass',
            first_name='Carlos',
            last_name='Mendes',
            tipo=User.Tipo.PROFESSOR,
        )
        self.professor = Professor.objects.create(
            usuario=self.user, formacao='Doutorado', especialidade='Neurologia'
        )

        self.turma = Turma.objects.create(
            disciplina='Medicina Interna',
            semestre='2023.2',
            capacidade_maxima=30,
            quantidade_alunos=25,
            professor_responsavel=self.professor,
        )

        self.caso = CasoClinico.objects.create(
            titulo='Caso Cardíaco',
            descricao='Paciente com dor torácica',
            area='Cardiologia',
            professor_responsavel=self.professor,
        )

        self.caso = CasoClinico.objects.create(
            titulo='Caso Cardíaco',
            descricao='Paciente com dor torácica',
            area='Cardiologia',
            professor_responsavel=self.professor
        )

        # Criar diagnóstico associado
        self.diagnostico = Diagnostico.objects.create(
            descricao='Diagnóstico correto',
            caso_clinico=self.caso,
            resposta_professor=self.professor
        )

    def test_professor_profile(self):
        url = reverse('info_perfil_prof', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['nome'], 'Carlos Mendes')
        self.assertEqual(response.json()['especialidade'], 'Neurologia')

    def test_professor_classes(self):
        url = reverse('listar_turmas_prof', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['disciplina'], 'Medicina Interna')

    def test_professor_cases(self):
        url = reverse('listar_casos_prof', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['título'], 'Caso Cardíaco')

    def test_case_details(self):
        url = reverse('info_casos', args=[self.user.id, self.caso.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['título'], 'Caso Cardíaco')
        self.assertIn('dor torácica', response.json()['descrição'])


class ExamSystemTests(APITestCase):
    def setUp(self):
        # Create users
        self.prof_user = User.objects.create_user(
            username='exam_prof',
            email='exam_prof@example.com',
            password='profpass',
            first_name='Exam',
            last_name='Professor',
            tipo=User.Tipo.PROFESSOR,
        )
        self.professor = Professor.objects.create(
            usuario=self.prof_user, formacao='PhD', especialidade='Education'
        )

        self.student_user = User.objects.create_user(
            username='exam_student',
            email='exam_student@example.com',
            password='studentpass',
            first_name='Exam',
            last_name='Student',
            tipo=User.Tipo.ALUNO,
        )
        self.student = Aluno.objects.create(usuario=self.student_user, semestre='2023.1')

        # Create class and team
        self.turma = Turma.objects.create(
            disciplina='Test Discipline',
            semestre='2023.1',
            capacidade_maxima=40,
            quantidade_alunos=35,
            professor_responsavel=self.professor,
        )
        self.turma.alunos_matriculados.add(self.student)

        self.team = Equipe.objects.create(nome='Team Alpha', turma=self.turma)
        self.team.alunos.add(self.student)

        # Create exams
        now = timezone.now()
        self.irat = Exame.objects.create(
            turma=self.turma,
            tipo='TBL',
            titulo='iRAT Test',
            descricao='Individual readiness test',
            deadline=now + timedelta(days=1),
            professor=self.professor,
        )

        self.grat = Exame.objects.create(
            turma=self.turma,
            tipo='TBL',
            titulo='gRAT Test',
            descricao='Group readiness test',
            deadline=now + timedelta(days=1),
            professor=self.professor,
            fase_associada=self.irat,
        )

        # Create questions
        self.mc_question = Questao.objects.create(
            exame=self.irat, enunciado='What is 2+2?', tipo='ME', valor_total=10.0
        )

        # Create alternatives
        self.alt1 = Alternativa.objects.create(questao=self.mc_question, texto='3', correta=False)
        self.alt2 = Alternativa.objects.create(questao=self.mc_question, texto='4', correta=True)

        # Login as student for some tests
        self.client.force_authenticate(user=self.student_user)

    def test_create_exam(self):
        self.client.force_authenticate(user=self.prof_user)
        url = reverse('exames-list')
        data = {
            'turma': self.turma.id,
            'tipo': 'PBL',
            'titulo': 'New PBL Exam',
            'descricao': 'Problem-based learning assessment',
            'deadline': (timezone.now() + timedelta(days=7)).isoformat(),
            'professor': self.professor.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exame.objects.count(), 3)

    def test_submit_answer(self):
        url = reverse('resposta-list', kwargs={'turma_pk': self.turma.id, 'exame_pk': self.irat.id})
        data = {'questao': self.mc_question.id, 'alternativa': self.alt2.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify answer was recorded
        answer = Resposta.objects.first()
        self.assertEqual(answer.alternativa, self.alt2)
        self.assertEqual(answer.aluno, self.student)

    def test_score_calculation(self):
        # Submit correct answer
        Resposta.objects.create(questao=self.mc_question, aluno=self.student, alternativa=self.alt2)

        # Release scores
        self.client.force_authenticate(user=self.prof_user)
        url = reverse('exames-liberar-notas', args=[self.irat.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify score
        score = NotaAvaliacao.objects.get(aluno=self.student, exame=self.irat, tipo='iRAT')
        self.assertEqual(score.valor, 10.0)

    def test_compound_score_calculation(self):
        # Create exam components
        nota_composta = NotaComposta.objects.create(nome='Final Grade', turma=self.turma)

        ComponenteNotaComposta.objects.create(
            nota_composta=nota_composta, exame=self.irat, peso=0.5
        )

        ComponenteNotaComposta.objects.create(
            nota_composta=nota_composta, exame=self.grat, peso=0.5
        )

        # Create scores
        NotaAvaliacao.objects.create(aluno=self.student, exame=self.irat, tipo='iRAT', valor=8.0)

        NotaAvaliacao.objects.create(equipe=self.team, exame=self.grat, tipo='gRAT', valor=9.0)

        # Calculate compound score
        self.client.force_authenticate(user=self.prof_user)
        url = reverse('notascompostas-calcular', args=[nota_composta.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify result
        result = ResultadoNotaComposta.objects.get(aluno=self.student, nota_composta=nota_composta)
        self.assertEqual(result.valor, 8.5)  # (8*0.5) + (9*0.5)

    def test_grat_penalty_calculation(self):
        # Create iRAT scores (average will be 80%)
        NotaAvaliacao.objects.create(aluno=self.student, exame=self.irat, tipo='iRAT', valor=8.0)

        # Create gRAT score that's significantly lower
        NotaAvaliacao.objects.create(
            equipe=self.team,
            exame=self.grat,
            tipo='gRAT',
            valor=6.0,  # 20% below iRAT average
        )

        # Calculate compound score with penalty
        nota_composta = NotaComposta.objects.create(nome='Test Grade', turma=self.turma)
        ComponenteNotaComposta.objects.create(
            nota_composta=nota_composta, exame=self.grat, peso=1.0
        )

        # Should apply penalty to gRAT score
        result = ResultadoNotaComposta.calcular_para_aluno(self.student, nota_composta)
        self.assertLess(result.valor, 6.0)  # Penalized score
        self.assertGreater(result.valor, 0)  # But still positive


class ModelValidationTests(TestCase):
    def setUp(self):
        # Create professor
        self.user = User.objects.create_user(
            username='test_prof',
            email='test_prof@example.com',
            password='testpass',
            first_name='Test',
            last_name='Professor',
            tipo=User.Tipo.PROFESSOR,
        )
        self.professor = Professor.objects.create(
            usuario=self.user, formacao='Doutorado', especialidade='Neurologia'
        )

        # Create class
        self.turma = Turma.objects.create(
            disciplina='Test Discipline',
            semestre='2023.1',
            capacidade_maxima=10,
            quantidade_alunos=0,
            professor_responsavel=self.professor,
        )

    def test_exam_status(self):
        # Test open exam
        exam = Exame.objects.create(
            turma=self.turma,
            tipo='TBL',
            titulo='Test Exam',
            deadline=timezone.now() + timedelta(days=1),
            professor=self.professor,
        )
        self.assertTrue(exam.aberto)

        # Test closed exam
        exam.deadline = timezone.now() - timedelta(days=1)
        exam.save()
        self.assertFalse(exam.aberto)

    def test_answer_validation(self):
        # Create exam and question
        exam = Exame.objects.create(
            turma=self.turma,  # Adicionar turma
            tipo='TBL',
            titulo='Validation Exam',
            deadline=timezone.now() + timedelta(days=1),
            professor=self.professor,  # Adicionar professor
        )

        # Create multiple choice question
        mc_question = Questao.objects.create(
            exame=exam, enunciado='MCQ Test', tipo='ME', valor_total=10
        )

        # Should require alternative for MCQ
        answer = Resposta(questao=mc_question)
        with self.assertRaises(ValidationError):
            answer.clean()

        # Create subjective question
        sub_question = Questao.objects.create(
            exame=exam, enunciado='Subjective Test', tipo='SUB', valor_total=10
        )

        # Should require text for subjective
        answer = Resposta(questao=sub_question)
        with self.assertRaises(ValidationError):
            answer.clean()


class SecurityTests(APITestCase):
    def test_authentication_requirements(self):
        # Create protected URLs
        exam_list_url = reverse('exames-list')
        resposta_list_url = reverse('resposta-list', kwargs={'turma_pk': 1, 'exame_pk': 1})

        # Unauthenticated access
        response = self.client.get(exam_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(resposta_list_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Create student user
        student_user = User.objects.create_user(
            username='security_student',
            email='security@student.com',
            password='studentpass',
            tipo=User.Tipo.ALUNO,
        )
        self.client.force_authenticate(user=student_user)

        # Student should see only their exams
        response = self.client.get(exam_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No exams created

    def test_role_based_access(self):
        # Create professor
        prof_user = User.objects.create_user(
            username='security_prof',
            email='security@prof.com',
            password='profpass',
            tipo=User.Tipo.PROFESSOR,
        )
        professor = Professor.objects.create(
            usuario=prof_user, formacao='PhD', especialidade='Security'
        )

        # Create student
        student_user = User.objects.create_user(
            username='security_student2',
            email='security2@student.com',
            password='studentpass',
            tipo=User.Tipo.ALUNO,
        )
        student = Aluno.objects.create(usuario=student_user)

        # Create class and exam
        turma = Turma.objects.create(
            disciplina='Security Class',
            semestre='2023.1',
            capacidade_maxima=20,
            quantidade_alunos=1,
            professor_responsavel=professor,
        )
        turma.alunos_matriculados.add(student)

        _exam = Exame.objects.create(
            turma=turma,
            tipo='TBL',
            titulo='Security Exam',
            deadline=timezone.now() + timedelta(days=1),
            professor=professor,
        )

        # Student can't access professor-only endpoints
        self.client.force_authenticate(user=student_user)
        url = reverse('notascompostas-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Professor can access
        self.client.force_authenticate(user=prof_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PerformanceTests(APITestCase):
    def setUp(self):
        # Create professor
        self.prof_user = User.objects.create_user(
            username='perf_prof',
            email='perf@prof.com',
            password='profpass',
            tipo=User.Tipo.PROFESSOR,
        )
        self.professor = Professor.objects.create(usuario=self.prof_user)

        # Create class
        self.turma = Turma.objects.create(
            disciplina='Performance Class',
            semestre='2023.1',
            capacidade_maxima=100,
            quantidade_alunos=100,
            professor_responsavel=self.professor,
        )

        # Create students
        self.students = []
        for i in range(100):
            student_user = User.objects.create_user(
                username=f'student_{i}',
                email=f'student_{i}@example.com',
                password='studentpass',
                tipo=User.Tipo.ALUNO,
            )
            student = Aluno.objects.create(usuario=student_user)
            self.students.append(student)
            self.turma.alunos_matriculados.add(student)

        # Create exam
        self.exam = Exame.objects.create(
            turma=self.turma,
            tipo='TBL',
            titulo='Performance Exam',
            deadline=timezone.now() + timedelta(days=1),
            professor=self.professor,
        )

        # Create questions
        self.questions = []
        for i in range(20):
            question = Questao.objects.create(
                exame=self.exam, enunciado=f'Question {i + 1}', tipo='ME', valor_total=5.0
            )
            self.questions.append(question)

            # Create alternatives
            for j in range(4):
                correct = j == 0
                Alternativa.objects.create(
                    questao=question, texto=f'Option {j + 1}', correta=correct
                )

        # Login as professor
        self.client.force_authenticate(user=self.prof_user)

    def test_mass_score_calculation(self):
        # Release scores endpoint
        url = reverse('exames-liberar-notas', args=[self.exam.id])

        # Time the request
        import time

        start_time = time.time()
        response = self.client.post(url)
        end_time = time.time()

        # Verify success
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify all scores created
        self.assertEqual(NotaAvaliacao.objects.count(), 100)

        # Performance check (should complete in reasonable time)
        self.assertLess(end_time - start_time, 5)  # Less than 5 seconds

    def test_compound_score_performance(self):
        # Create compound grade
        nota_composta = NotaComposta.objects.create(nome='Final Grade', turma=self.turma)
        ComponenteNotaComposta.objects.create(
            nota_composta=nota_composta, exame=self.exam, peso=1.0
        )

        # Calculate endpoint
        url = reverse('notascompostas-calcular', args=[nota_composta.id])

        # Time the request
        import time

        start_time = time.time()
        response = self.client.post(url)
        end_time = time.time()

        # Verify success
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify all results created
        self.assertEqual(ResultadoNotaComposta.objects.count(), 100)

        # Performance check
        self.assertLess(end_time - start_time, 3)  # Less than 3 seconds
