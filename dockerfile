FROM python:3.11

# デバッグ用
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "src/main.py", "--server.address=0.0.0.0"]
