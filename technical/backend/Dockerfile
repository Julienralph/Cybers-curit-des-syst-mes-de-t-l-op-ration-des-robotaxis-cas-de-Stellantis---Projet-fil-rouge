FROM python:3.11-slim

# ========================================================================
# DOCKERFILE — Backend FastAPI
# ========================================================================
# Image de base : Python 3.11-slim (léger, ~150MB vs 900MB full)
# ========================================================================

WORKDIR /app

# Copie les dépendances
COPY requirements.txt .

# Installe les dépendances (avec cache optimization)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copie le code source
COPY . .

# Crée le dossier pour les logs
RUN mkdir -p /app/logs

# Expose le port FastAPI
EXPOSE 8000

# Commande de démarrage
# uvicorn = serveur ASGI (async)
# --host 0.0.0.0 = écoute sur toutes les interfaces (important en Docker)
# --port 8000 = port exposé
# --reload = rechargement auto en dev (à retirer en prod)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/certs/server.key", "--ssl-certfile", "/certs/server.crt"]
