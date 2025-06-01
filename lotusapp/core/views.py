from django.http import JsonResponse
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from .models import Usuario, Aluno, Professor

@csrf_exempt
@require_http_methods(["POST"])
def cadastro(request):
    try:
        data = json.loads(request.body)

        nome = data.get('nome')
        cpf = data.get('cpf')
        email = data.get('email')
        senha = data.get('senha')
        foto_url = data.get('foto_url', '') 
        tipo_usuario = data.get('tipo')

        #TODO: fazer Validações

        # Hashear a senha antes de salvar
        senha_hash = make_password(senha)
        data_atual = timezone.now().date()

        user_data_dict = {
            'nome': nome,
            'cpf': cpf,
            'email': email,
            'senha': senha_hash,
            'foto_url': foto_url,
            'data_cadastro': data_atual,
        }

        novo_usuario = None
        if tipo_usuario == Usuario.Tipo.ALUNO:
            user_data_dict['semestre'] = data.get('semestre', 'N/A') 
            user_data_dict['ira'] = data.get('ira', 0.0)    
            novo_usuario = Aluno.objects.create(**user_data_dict)
        
        elif tipo_usuario == Usuario.Tipo.PROFESSOR:
            user_data_dict['formacao'] = data.get('formacao', 'N/A') 
            user_data_dict['especialidade'] = data.get('especialidade', 'N/A') 
            novo_usuario = Professor.objects.create(**user_data_dict)
        elif tipo_usuario == Usuario.Tipo.ADMINISTRADOR:
            user_data_dict['tipo'] = Usuario.Tipo.ADMINISTRADOR # Define explicitamente para admin
            novo_usuario = Usuario.objects.create(**user_data_dict)
        else:
            # Caso não seja encontra um tipo de usuário válido
            return JsonResponse({'erro': 'Tipo de usuário inválido.'}, status=400)

        return JsonResponse({
            # TODO:Mensagem de confirmação, sera que seguro passar id? Porém ajudaria no desenvolvimento
            'mensagem': 'Usuário cadastrado com sucesso!',
            'usuario': {
                'id': novo_usuario.id,
                'nome': novo_usuario.nome,
                'email': novo_usuario.email,
                'tipo': novo_usuario.tipo
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': f'ocoorreu: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        senha_fornecida = data.get('senha')

        if not email or not senha_fornecida:
            return JsonResponse({'erro': 'Email e senha são obrigatórios.'}, status=400)
        try:
            # BUscando o usuário pelo email fornecido
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return JsonResponse({'erro': 'Usuário não encontrado.'}, status=404)

        if check_password(senha_fornecida, usuario.senha):
            # TODO: Implementar autenticação JWT futuramente

            user_data_response = {
                'id': usuario.id,
                'nome': usuario.nome,
                'email': usuario.email,
                'tipo': usuario.tipo,
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
        return JsonResponse({'erro': f'Ocorreu um erro: {str(e)}'}, status=500)