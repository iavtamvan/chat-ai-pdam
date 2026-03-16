#docker compose stop backend frontend ollama redis
docker compose down -v
#docker rm pdam-backend pdam-frontend pdam-ollama pdam-redis
docker compose build --no-cache redis ollama backend frontend
docker compose up -d ollama redis backend frontend