FROM nginx:1.27-alpine

RUN rm -f /etc/nginx/conf.d/default.conf
COPY docker/web_default.conf.template /etc/nginx/templates/default.conf.template
COPY web_client /usr/share/nginx/html
