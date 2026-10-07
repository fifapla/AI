FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .
EXPOSE 8080
ENV BIND_HOST=0.0.0.0
CMD ["python", "-m", "ragkit", "serve", "--port", "8080"]
