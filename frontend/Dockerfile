FROM node:20-alpine

WORKDIR /usr/app


COPY package.json package-lock.json ./
RUN npm ci --silent  


RUN npm install -g react-scripts


COPY . .


RUN chown -R node:node /usr/app && \
    chmod -R 755 /usr/app


USER node

CMD ["npm", "start"]