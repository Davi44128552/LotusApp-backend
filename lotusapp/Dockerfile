# Utlização da versão slim que diminui o tamanho da imagem
FROM python:3.10-slim AS builder

RUN mkdir /app

WORKDIR /app

# Variáveis de ambiente para otimizar o Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

RUN pip install --upgrade pip 

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Segundo estágio do multi-stage build
FROM python:3.10-slim

RUN useradd -m -r appuser && \
   mkdir /app && \
   chown -R appuser /app

# Copiando os as dependências instaladas no estágio anterior
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app

# Copiando o código da aplicação
COPY --chown=appuser:appuser . .

# Variáveis de ambiente para otimizar o Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh

# Alterando o usuário para não rodar como root (Segurannça)
USER appuser

EXPOSE 8000 

ENTRYPOINT ["/app/entrypoint.sh"]

# Comando para rodar a aplicação
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]