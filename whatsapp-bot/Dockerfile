# PDAM WhatsApp Bot Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Create sessions directory
RUN mkdir -p /app/sessions

# Environment
ENV NODE_ENV=production
ENV API_URL=http://backend:8000
ENV SESSION_DIR=/app/sessions

EXPOSE 3001

CMD ["npm", "start"]
