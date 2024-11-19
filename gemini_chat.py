import os
import google.generativeai as genai
import dotenv

dotenv.load_dotenv()

# 環境変数からGemini APIキーを取得
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# モデルの設定
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# モデルの初期化
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-002",
    generation_config=generation_config,
)

# チャットセッションの開始
chat_session = model.start_chat(history=[])
