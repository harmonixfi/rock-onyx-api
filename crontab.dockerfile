FROM python:3.10-alpine

# Set the timezone to UTC
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Update the package repository and install curl
RUN apk update && apk add curl bash tzdata nano

WORKDIR /app/

ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.1.5/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=9aeb41e00cc7b71d30d33c57a2333f2c2581a201

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

RUN pip install --force-reinstall httpcore==0.15

RUN curl -fsSLO "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
    && chmod +x "$SUPERCRONIC" \
    && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
    && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

# For development, Jupyter remote kernel, Hydrogen
# Using inside the container:
# jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.custom_display_url=http://127.0.0.1:8888
ARG INSTALL_JUPYTER=false
RUN bash -c "if [ $INSTALL_JUPYTER == 'true' ] ; then pip install jupyterlab ; fi"

# Create logs directory if it doesn't exist
RUN mkdir -p /app-logs/

# Copy crontab file
COPY ./crontab /app/crontab

COPY supercronic_entry.sh /usr/local/bin/supercronic.sh
RUN chmod +x /usr/local/bin/supercronic.sh

COPY ./src /app
ENV PYTHONPATH=/app

ARG SEQ_SERVER_API_KEY
RUN sed -i "s/{{SEQ_SERVER_API_KEY}}/${SEQ_SERVER_API_KEY}/g" /app/config/seqlog.yml

ENTRYPOINT ["/usr/local/bin/supercronic.sh"]