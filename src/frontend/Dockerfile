# 使用 Python 3.10 作為基礎映像
FROM python:3.10

# 設定環境變數
ENV PYTHONUNBUFFERED True
ENV APP_HOME /back-end

# 設定工作目錄
WORKDIR $APP_HOME

# 更新套件列表並安裝必要的系統套件
RUN apt-get update && \
    apt-get install -qy nano sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 複製本地代碼到容器內
COPY . ./

# 安裝 Python 套件
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 設定啟動命令 (前面是flask檔名)
# CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 home:app
CMD ["python3", "/back-end/home.py"]
