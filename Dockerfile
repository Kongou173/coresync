#pythonイメージを取得
FROM python:3.10

# 作業ディレクトリを設定
WORKDIR /app

# 必要なファイルをコピー
COPY . .

# 依存関係のインストール
RUN pip install -r requirements.txt

# コンテナ起動時のコマンド
CMD ["python", "main.py"]
