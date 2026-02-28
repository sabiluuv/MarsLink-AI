import os
import requests
from flask import Flask, request, Response, send_from_directory
from dotenv import load_dotenv

# Загружаем переменные (DEEPSEEK_API_KEY) из файла .env
load_dotenv()

# Инициализируем Flask, указываем текущую папку как папку со статикой
app = Flask(__name__, static_folder='.', static_url_path='')

# 1. Раздаем наш фронтенд (index.html)
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# 2. Обрабатываем запросы к нашему API
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Обработка CORS (на всякий случай)
    if request.method == 'OPTIONS':
        return '', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return {"error": "DEEPSEEK_API_KEY is not configured in .env"}, 500

    data = request.json
    if not data or 'messages' not in data:
        return {"error": "Invalid request: messages array required"}, 400

    # Формируем тело запроса для DeepSeek
    deepseek_body = {
        "model": data.get("model", "deepseek-chat"),
        "messages": data["messages"],
        "max_tokens": data.get("max_tokens", 2048),
        "temperature": data.get("temperature", 0.7),
        "stream": True # Включаем потоковую передачу
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        # Отправляем запрос к DeepSeek
        deepseek_response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=deepseek_body,
            stream=True # Важно для стриминга ответа!
        )

        # Если ошибка от DeepSeek — прокидываем её
        if deepseek_response.status_code != 200:
            return Response(deepseek_response.text, status=deepseek_response.status_code, mimetype='application/json')

        # Функция-генератор для непрерывной передачи кусков текста (SSE)
        def generate():
            for chunk in deepseek_response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk

        # Возвращаем потоковый ответ обратно в наш браузер
        return Response(
            generate(), 
            status=200, 
            content_type=deepseek_response.headers.get('Content-Type', 'text/event-stream')
        )

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    print("🚀 Сервер запущен! Откройте в браузере: http://127.0.0.1:8888")
    app.run(host='127.0.0.1', port=8888, debug=True)