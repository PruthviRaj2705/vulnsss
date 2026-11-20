# Old base image with many OS CVEs (Trivy image scan)
FROM python:3.6
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Trivy misconfig: runs as root, no HEALTHCHECK, hardcoded secret in ENV
ENV DB_PASSWORD=admin123
EXPOSE 5000
CMD ["python", "vulnerable_app.py"]
