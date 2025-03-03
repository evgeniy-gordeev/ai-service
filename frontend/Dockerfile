# Этап сборки
FROM node:18-alpine as build

WORKDIR /app

# Переменные окружения
ENV TSC_COMPILE_ON_ERROR=true \
    ESLINT_NO_DEV_ERRORS=true \
    DISABLE_ESLINT_PLUGIN=true \
    NODE_OPTIONS=--max_old_space_size=4096 \
    GENERATE_SOURCEMAP=false

# Копируем файлы зависимостей
COPY package.json ./

# Оптимизированная установка зависимостей (обычный npm install вместо npm ci)
RUN npm install --production --no-audit --prefer-offline && \
    npm cache clean --force

# Копируем только необходимые файлы исходного кода
COPY public ./public
COPY src ./src
COPY tsconfig.json ./

# Оптимизированная сборка для production
RUN npm run build

# Этап production - используем легковесный nginx-alpine
FROM nginx:alpine as production

# Копируем только собранные файлы и конфигурацию
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Оптимизация Nginx
RUN echo 'gzip on; \
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;' > /etc/nginx/conf.d/gzip.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
