FROM nginx:alpine

ARG ENVIRONMENT_NAME

RUN apk update && apk add bash
RUN apk add apache2-utils

RUN echo ${ENVIRONMENT_NAME}

COPY nginx.$ENVIRONMENT_NAME.conf /etc/nginx/nginx.conf
