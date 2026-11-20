FROM python:3.12-slim

WORKDIR /app
COPY fsociety_toolkit_v1.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "fsociety_toolkit_v1.py"]
