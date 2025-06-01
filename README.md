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
  python3 manage.py migrate
  python3 manage.py createsuperuser
  python3 manage.py runserver
  ```
(Atualmente dokcer esta com problema, rode sem!)
* Faça o build do container e rode
  ```bash
  docker compose up --build
  ```
* Futuramente é possível apenas iniciar o container ja construido com
  ```bash
  docker compose up
  ```
* Ao fechar o temrinal também não é ncessesário criar um novo ambiente virtual, apenas executar o existente já é suficiente
