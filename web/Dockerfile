FROM node:22-alpine AS build

WORKDIR /app
COPY web/ ./web/
COPY contracts/ ./contracts/

WORKDIR /app/web
RUN npm ci
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

FROM nginx:1.27-alpine

COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/web/dist/ /usr/share/nginx/html/
EXPOSE 80
