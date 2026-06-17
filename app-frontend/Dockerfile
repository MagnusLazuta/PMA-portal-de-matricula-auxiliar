# Estágio 1: Construir a aplicação Vue com Node
FROM node:20-alpine AS build-stage

WORKDIR /app

# Copia arquivos de definição de dependências
COPY package*.json ./

# Instala dependências
RUN npm install

# Copia todo o código-fonte do frontend
COPY . .

# Compila o projeto para produção
RUN npm run build

# Estágio 2: Servir os arquivos estáticos com Nginx
FROM nginx:stable-alpine AS production-stage

# Copia a build do estágio 1 para a pasta pública do Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expõe a porta padrão do Nginx (80)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
