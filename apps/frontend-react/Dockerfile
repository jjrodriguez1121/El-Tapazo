# syntax=docker/dockerfile:1

# --------------------------------------------------------------------------- #
# Desarrollo: servidor de Vite con hot reload
# --------------------------------------------------------------------------- #
FROM node:24-alpine AS development

WORKDIR /app

# Se copian solo los manifiestos para aprovechar la caché de capas de Docker.
COPY package*.json ./
# La huella le cuenta a scripts/entrypoint.sh que estas dependencias ya están al
# día, para que no las vuelva a instalar en el primer arranque.
RUN npm ci && sha256sum package-lock.json | cut -d ' ' -f 1 > node_modules/.huella-package-lock

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# --------------------------------------------------------------------------- #
# Build de producción
# --------------------------------------------------------------------------- #
FROM node:24-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# --------------------------------------------------------------------------- #
# Producción: los estáticos servidos por nginx
# --------------------------------------------------------------------------- #
FROM nginx:1.29-alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
