FROM python:3.12-alpine
RUN apk add --no-cache tar rsync gzip
# Docker CLI + Compose plugin, to drive the Minecraft servers from inside the container.
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:27-cli /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.34.0 pyyaml==6.0.2 bcrypt==4.2.1
WORKDIR /app
COPY app/ /app/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
