FROM python:3.14-slim
# defining dedicated work directory inside container (can be any name other than OS level directories)
WORKDIR /app

# mounting and installing requirements with cache instead of copying since they are only required once
RUN --mount=type=bind,source=src/requirements.txt,target=/tmp/requirements.txt \
    --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r /tmp/requirements.txt

# copying the source code and exposing the port
COPY . .
RUN mkdir -p /app/data
EXPOSE 8080

# setting up environment path for python (path to look for imports)
ENV PYTHONPATH=/app/src

# this is for proper Docker logging
ENV PYTHONUNBUFFERED=1

# transferring ownership to app user for logging permission
RUN useradd app && chown -R app:app /app
USER app

# executable and its args (ENTRPOINT + CMD), args are changable at runtime
ENTRYPOINT [ "uvicorn" ]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8080"]