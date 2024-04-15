FROM nginx:latest

RUN mkdir -p /etc/letsencrypt /var/www/letsencrypt /etc/nginx/ssl

COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 8080 443