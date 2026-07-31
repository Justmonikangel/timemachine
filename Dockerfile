FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY config ./config
ENV ACA_POLICY_PATH=/app/policy.yaml
EXPOSE 8000
CMD ["aca", "serve", "--host", "0.0.0.0", "--port", "8000"]
