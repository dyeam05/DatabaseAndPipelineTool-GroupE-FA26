FROM node:24-alpine AS base

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

# Development stage — runs Vite dev server with HMR
FROM base AS dev

EXPOSE 5173

CMD ["npm", "run", "dev"]

# Build stage — produces static assets
FROM base AS builder

RUN npm run build

# Production stage — serves built assets with nginx
FROM nginx:alpine AS prod

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
