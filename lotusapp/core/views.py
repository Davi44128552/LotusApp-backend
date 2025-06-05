from django.http import JsonResponse
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import  check_password
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import Usuario, Aluno, Professor

@csrf_exempt
@require_http_methods(["POST"])
def cadastro(request):
    try:
        data = json.loads(request.body)

        # dados recebidos do post
        first_name = data.get('nome') 
        last_name = data.get('sobrenome', '') 
        cpf = data.get('cpf')
        email = data.get('email')
        password = data.get('senha') 
        username = data.get('username') 
        foto_url = data.get('foto_url', '')
        tipo_usuario_str = data.get('tipo') 

        if not all([first_name, cpf, email, password, username, tipo_usuario_str]):
            return JsonResponse({'erro': 'Campos obrigatórios ausentes (nome, cpf, email, senha, username, tipo).'}, status=400)

        # Verificar se o usuário (email ou username ou cpf) já existe
        if Usuario.objects.filter(email=email).exists():
            return JsonResponse({'erro': 'Este email já está cadastrado.'}, status=400)
        if Usuario.objects.filter(username=username).exists():
            return JsonResponse({'erro': 'Este nome de usuário já está em uso.'}, status=400)
        if Usuario.objects.filter(cpf=cpf).exists():
            return JsonResponse({'erro': 'Este CPF já está cadastrado.'}, status=400)

        user_creation_data = {
            'first_name': first_name,
            'last_name': last_name,
            'cpf': cpf,
            'foto_url': foto_url,
        }

        try:
            novo_usuario_obj = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                **user_creation_data
            )
        except ValueError as ve: 
            return JsonResponse({'erro': str(ve)}, status=400)

        # Perfil de aluno
        if tipo_usuario_str == Usuario.Tipo.ALUNO.value: 
            novo_usuario_obj.tipo = Usuario.Tipo.ALUNO
            novo_usuario_obj.save()
            Aluno.objects.create(
                usuario=novo_usuario_obj,
                semestre=data.get('semestre', 'N/A'),
                ira=data.get('ira', 0.0)
            )
        # Perfil de professor
        elif tipo_usuario_str == Usuario.Tipo.PROFESSOR.value: 
            novo_usuario_obj.tipo = Usuario.Tipo.PROFESSOR
            novo_usuario_obj.save()
            Professor.objects.create(
                usuario=novo_usuario_obj,
                formacao=data.get('formacao', 'N/A'),
                especialidade=data.get('especialidade', 'N/A')
            )
        elif tipo_usuario_str == Usuario.Tipo.ADMINISTRADOR.value:
            novo_usuario_obj.tipo = Usuario.Tipo.ADMINISTRADOR
            novo_usuario_obj.is_staff = True
            novo_usuario_obj.is_superuser = data.get('is_superuser', False) # Para criar admins sem permissões de superusuário
            novo_usuario_obj.save()
        else:
            # Caso não cosniga achar o tipo eu deleto o usuario criado
            novo_usuario_obj.delete() 
            return JsonResponse({'erro': 'Tipo de usuário inválido fornecido.'}, status=400)

        return JsonResponse({
            'mensagem': 'Usuário cadastrado com sucesso!',
            'usuario': {
                'id': novo_usuario_obj.id,
                'first_name': novo_usuario_obj.first_name,
                'email': novo_usuario_obj.email,
                'username': novo_usuario_obj.username,
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        senha_fornecida = data.get('senha')

        if not email or not senha_fornecida:
            return JsonResponse({'erro': 'Email e senha são obrigatórios.'}, status=400)
        
        usuario = authenticate(request, username=email, password=senha_fornecida)

        if usuario is not None:
        
            user_data_response = {
                'id': usuario.id,
                'first_name': usuario.first_name,
                'last_name': usuario.last_name,
                'email': usuario.email,
            }


            return JsonResponse({
                'mensagem': 'Login bem-sucedido!',
                'usuario': user_data_response
                # TODO: Token seria retornado aqui
            }, status=200)
        else:
            # Senha incorreta
            return JsonResponse({'erro': 'Credenciais inválidas.'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)