FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install --frozen-lockfile
COPY . .
# ENV NODE_ENV production
# RUN npm run build
ENV PORT 3000
EXPOSE 3000
CMD ["npm", "start"]
USER node
