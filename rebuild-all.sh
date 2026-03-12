docker compose stop backend frontend
docker rm pdam-backend pdam-frontend
docker compose build --no-cache backend frontend
docker compose up -d backend frontend