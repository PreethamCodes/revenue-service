FROM python:3.12-slim AS probe
WORKDIR /probe
COPY config/health.txt .
USER nobody
ENV PORT=3001
CMD ["sh","-c","exec python -m http.server \"$PORT\" --bind 0.0.0.0 --directory /probe"]

FROM python:3.12-slim AS backend
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PORT=8001
COPY requirements.txt requirements-db.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py runtime.py ./
COPY contracts ./contracts
USER nobody
CMD ["sh","-c","exec uvicorn app:app --host 0.0.0.0 --port \"$PORT\" --no-access-log"]
