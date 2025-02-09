FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN apt update && apt upgrade -y

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "Python file.py"]