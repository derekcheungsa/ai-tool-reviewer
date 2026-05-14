FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-builder /app/.next ./.next/
COPY --from=frontend-builder /app/node_modules ./node_modules/
COPY --from=frontend-builder /app/package.json ./
COPY --from=frontend-builder /app/public ./public/
COPY start.sh ./
RUN chmod +x start.sh
ENV PORT=3000
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
EXPOSE 3000
CMD ["./start.sh"]
