FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix /install -r requirements.txt

FROM python:3.13-slim
WORKDIR /usr/src/app
COPY --from=builder /install /usr/local
COPY metar.py .
CMD ["python", "./metar.py"]
