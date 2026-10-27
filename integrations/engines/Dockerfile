FROM node:22-alpine

WORKDIR /app/integrations/engines
COPY integrations/engines/package.json integrations/engines/package-lock.json ./
RUN npm ci

COPY integrations/engines/tsconfig.json integrations/engines/NOTICE integrations/engines/API.md ./
COPY integrations/engines/src ./src
COPY integrations/engines/vendor ./vendor
COPY integrations/engines/scripts ./scripts
COPY integrations/engines/vendor-manifest.json ./vendor-manifest.json
COPY contracts/api /app/contracts/api
RUN mkdir /data && chown node:node /data

ENV ENGINES_HOST=0.0.0.0
ENV ENGINES_PORT=8790
ENV ENGINES_DATA_DIR=/data
VOLUME ["/data"]
EXPOSE 8790

USER node
CMD ["npm", "start"]
