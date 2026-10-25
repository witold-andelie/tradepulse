FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[agent]" \
    && useradd --create-home --uid 10001 tradepulse \
    && mkdir -p runs logs \
    && chown -R tradepulse:tradepulse /app

USER tradepulse
ENV SAMPLE_MODE=true
EXPOSE 8000
CMD ["python", "serve.py", "--host", "0.0.0.0", "--port", "8000"]
