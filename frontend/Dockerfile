FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Desarrollo: servidor de Vite con recarga en caliente (el código se monta como volumen).
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM deps AS build
COPY . .
RUN npm run build

# Producción: estáticos servidos por nginx, que hace de proxy de /api al backend.
FROM nginx:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
