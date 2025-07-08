FROM node:18 as build
WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm ci

COPY . .
RUN npm run build
RUN mkdir -p /result_build
RUN cp -r /app/build/. /result_build 
RUN npm install --global http-server

CMD ["npx", "-y", "http-server", "-p", "9100", "/app/build"]
