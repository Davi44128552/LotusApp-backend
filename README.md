# 🪷 LotusApp-backend
Dedicated repository for the development of the Lotus app's backend

## Django
The application’s backend is made in Python using the Django library. To ensure the backend runs correctly, you must have Django installed.

You can install it with one of these commands: `pip install django` or `sudo apt install python3-django`(Linux users only).

## Instruções para rodar o projeto:
* Ter docker instalado
* Entrar na pasta lotusapp
  ```
  cd lotusapp
  ```
* Criar ambiente virtual
  ```bash
  # Crie o ambiente virtual
  python -m venv venv
  
  # Ative o ambiente virtual
  # No Linux/macOS:
  source venv/bin/activate
  # No Windows:
  venv\Scripts\activate
  ```
* Crie um arquivo chamado `.env` e adicione o conteúdo de `.env.example` dentro
* Gere um nova secret key e adicione ao arquivo entre áspas, ela pode ser gerada [aqui](https://djecrety.ir/)
* Rodando sem docker
  ```bash
  pip install -r requirements.txt
  python3 manage.py makemigrations core # Pode ser necessario utilizar este comando primeiro para não dar erro na criação do superusuário
  python3 manage.py makemigrations
  python3 manage.py migrate
  python3 manage.py createsuperuser
  python3 manage.py runserver 0.0.0.0:8000
  ```

  *Obs.: Se der erro relacionado à inexistência das bibliotecas recém-instaladas, escreva apenas "python" no lugar de "python3"*

## Testando

1. Entre no `venv` (caso já não esteja): `source venv/bin/activate`
2. Instale a dependencias de teste: `python -r requirements-test.txt`
3. Rode os testes: `pytest --cov=core`
