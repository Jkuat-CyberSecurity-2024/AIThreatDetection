FROM nginx:latest
RUN apt-get update && \
    apt-get install -y libnginx-mod-http-vhost-traffic-status && \
    rm -rf /var/lib/apt/lists/*
COPY nginx.conf /etc/nginx/nginx.conf
