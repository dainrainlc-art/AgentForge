# Frontend Dockerfile - 最简版本
FROM nginx:alpine

# 只复制 index.html
COPY index.html /usr/share/nginx/html/index.html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
