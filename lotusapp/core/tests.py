from django.test import TestCase, Client
from django.urls import reverse
from .models import Usuario, Professor, Aluno, Nota, Turma


class CadastroLoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('register')

    def test_cadastro_professor(self):
        response = self.client.post(
            self.url,
            data={
                'nome': 'João',
                'sobrenome': 'Silva',
                'cpf': '12345678900',
                'email': 'joao@example.com',
                'senha': 'senha123',
                'username': 'joaosilva',
                'tipo': 'prof',
                'formacao': 'Medicina',
                'especialidade': 'Neurologia',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('usuario', response.json())

    def test_login_com_credenciais_validas(self):
        user = Usuario.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='senha123',
            first_name='Maria',
            last_name='Souza',
            cpf='98765432100',
        )
        user.tipo = Usuario.Tipo.ALUNO
        user.save()

        response = self.client.post(
            reverse('login'),
            data={'email': 'maria@example.com', 'senha': 'senha123'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('mensagem', response.json())


class NotasViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.prof_usuario = Usuario.objects.create_user(
            username='prof1',
            email='prof1@example.com',
            password='senha',
            first_name='Prof',
            last_name='Um',
            cpf='11111111111',
        )
        self.professor = Professor.objects.create(
            usuario=self.prof_usuario,
            formacao='Biologia',
            especialidade='Botânica',
        )

        self.aluno_usuario = Usuario.objects.create_user(
            username='aluno1',
            email='aluno1@example.com',
            password='senha',
            first_name='Aluno',
            last_name='Um',
            cpf='22222222222',
        )
        self.aluno = Aluno.objects.create(
            usuario=self.aluno_usuario,
            semestre='2025/1',
            matricula='A123456789',
        )

        self.turma = Turma.objects.create(
            disciplina='Botânica I',
            semestre='2025/1',
            capacidade_maxima=30,
            quantidade_alunos=1,
            professor_responsavel=self.professor,
        )
        self.turma.alunos_matriculados.add(self.aluno)

        self.nota1 = Nota.objects.create(valor=8.5)
        self.nota2 = Nota.objects.create(valor=9.0)
        self.aluno.notas.add(self.nota1, self.nota2)

    def test_listar_notas(self):
        url = reverse(
            'listar_notas', kwargs={'prof_id': self.prof_usuario.id, 'turma_id': self.turma.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['aluno'], 'Aluno Um')
        self.assertEqual(data[0]['notas'], [8.5, 9.0])
