FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY leaklens ./leaklens
RUN pip install --no-cache-dir ".[arena,app]"
EXPOSE 8000 8501
CMD ["uvicorn", "leaklens.api:app", "--host", "0.0.0.0", "--port", "8000"]