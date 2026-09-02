# ============================================================
# IBVAP — Frontend (React/Vite) Dockerfile
# Multi-stage: node builder -> nginx static server
# ============================================================

# ── Stage 1: builder ─────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install deps first (better layer caching)
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

# Copy source and build
COPY . .

# Build args — override in docker-compose for staging/prod
ARG VITE_API_URL=/api/v1
ARG VITE_WS_URL=

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

RUN npm run build


# ── Stage 2: production (nginx) ───────────────────────────────
FROM nginx:1.25-alpine AS production

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# SPA routing — serve index.html for all routes
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
