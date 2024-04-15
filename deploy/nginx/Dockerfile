FROM nginx:latest

RUN mkdir -p /etc/letsencrypt /var/www/letsencrypt /etc/nginx/ssl

COPY ./nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 8000 443
