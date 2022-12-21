# first stage builds vue
FROM node:19-alpine as build-stage
WORKDIR /app
COPY . .
RUN npm ci
RUN npm run build

# second stage copies only the static dist files to nginx html dir

FROM nginx:1.22-alpine AS prod

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

COPY --from=build-stage /app/dist /usr/share/nginx/html
