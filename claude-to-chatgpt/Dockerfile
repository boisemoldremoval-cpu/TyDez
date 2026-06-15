FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY claude_to_chatgpt ./claude_to_chatgpt

EXPOSE 8000

CMD ["uvicorn", "claude_to_chatgpt.app:app", "--host", "0.0.0.0", "--port", "8000"]
