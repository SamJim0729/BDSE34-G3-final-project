""" ====== 引用套件 ========== """
from flask import Flask, render_template, request, jsonify, abort, session
import json
from flask_session import Session
# 與作業系統進行互動
import os 

# CORS 是一種瀏覽器安全功能，用於允許或限制不同來源之間的資源請求
from flask_cors import CORS # 新加的

# 與 Line Bot 相關的套件
# Line Bot SDK 提供，用於處理 Line Bot 相關的操作和事件
from linebot import (LineBotApi, WebhookHandler)
# 異常類別，用於處理簽名驗證失敗的情況
from linebot.exceptions import (InvalidSignatureError)
# 來自 Line Messaging API 的 Python SDK，用於創建和處理 LINE 機器人消息
from linebot.models import *

# 引用 clean_function_flask 的重點函式 「function_call」
from clean_function_flask import function_call

# 引用 map檔案
import map as ma

# 從 .env 檔案中讀取環境變數並加載到運行環境中
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


""" Flask """
# 初始化 Flask 應用程式
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # Enable CORS for all routes and origins

# 防止中文變成 unicode 編碼
app.json.ensure_ascii = False

# Configure FLASK_DEBUG from environment variable
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

# 設置 secret key 和 session 類型
app.config['SECRET_KEY'] = 'your_secret_key' # 確保數據的安全性
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系統存儲session (指定會話數據的存儲方式)
Session(app)


""" Line Bot """
# # Line Bot 初始化
# # Line Bot - 放上 Channel Access Token (在 Messaging API)
# line_bot_api = LineBotApi('cmQza/w3HEukIwQkDnWHAZE91Z5jXtUz7iJliE1qNF7vFRBLdSGeGgRwOHIpd8LrZthj6DHKegPbp55P/MvRZeVhvPXSTJFslCmNf8miZ/+G+43h8VF0Rv808WXXNV36QIB6grG8wG6HMxTG0omb5gdB04t89/1O/w1cDnyilFU=')

# # Line Bot - 放上 Channel secret (在 Basic settings)
# handler = WebhookHandler('effcf596d1da798d55cf96d5dc5cca11')

# # Line Bot - 放上 Your user ID (在 Basic settings)
# line_bot_api.push_message('Ud2bf1e46315c04f519eff373640c4803', TextSendMessage(text='你可以開始了') )


# 首頁
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/home", methods=["GET"])
def home():
    return render_template("index.html")

# 趨勢分析
@app.route("/trend", methods=["GET"])
def trend():
    return render_template("trend.html")

# 迎避設施
@app.route("/map", methods=["GET", "POST"])
def map():
    return render_template("map.html")

# 迎避設施的 提交功能
@app.route('/submit', methods=['GET'])
def submit_data():
    # Retrieve data from the query parameters
    city = request.args.get('city')
    district = request.args.get('district')
    total_ping = request.args.get('total_ping')
    total_price= request.args.get('total_price')
    property_type = request.args.get('property_type')
    
    full_url = request.url
    print(full_url)

    # Combine all data into one response dictionary
    response = {
        'city': city,
        'district': district,
        'total_ping': total_ping,
        'total_price': total_price,
        'property_type' : property_type,
        'message': 'Data received successfully!'
    }
    
    pine_cone_json = json.loads(ma.main(full_url))
    print("pine_cone_json type:", type(pine_cone_json))
    print("pine_cone_json sample:", pine_cone_json[:2] if isinstance(pine_cone_json, list) else pine_cone_json)

    # Check if pine_cone_json is a list and not empty
    if isinstance(pine_cone_json, list) and len(pine_cone_json) > 0:
        # Extract details from each entry in the list
        extracted_data = []
        for item in pine_cone_json:
            house_images_string = item.get('房屋圖片', '[]')
            try:
                house_images_array = json.loads(house_images_string.replace("'", '"'))
                image_url = house_images_array[0] if house_images_array else '未提供'
            except json.JSONDecodeError:
                image_url = '未提供'

            parkinglot_string = item.get('含車位', '[]')
    
            if parkinglot_string == "0.0":
                parkinglot_string = "無車位"
            else:
                parkinglot_string = "有車位"
            # 如果你需要在處理後使用更新的 pine_cone_json，它現在包含了修改後的值
            extracted_details = {
                'index': item.get('index', '未提供'),
                'longitude': item.get('longtitude', '未提供'),  # 修正拼寫
                'latitude': item.get('latitude', '未提供'),
                '地址': item.get('地址', '未提供'),
                '含車位': parkinglot_string,
                '權狀坪數': item.get('權狀坪數', '未提供'),
                '屋齡': item.get('屋齡', '未提供'),
                '售價總價': item.get('售價總價', '未提供'),
                '模型_實際價格': item.get('模型_實際價格', '未提供'),
                '每坪售價': round(item.get('每坪售價', '未提供'), 2),
                '房屋圖片': image_url,
            }
            extracted_data.append(extracted_details)

        # Add extracted data to the response dictionary
        response['extracted_data'] = extracted_data
    else:
        response['message'] = 'No data found or data is not in expected format.'
        response['extracted_data'] = []

    print("Final response:", json.dumps(response, ensure_ascii=False, indent=2))
    return jsonify(response)

@app.route('/initial_data', methods=['GET'])
def get_initial_data():
    # 返回一些默認的或隨機的數據
    # EX: 返回所有數據的一個子集，或者某個特定區域的數據
    
    # 如: 返回前100條數據
    initial_data = get_sample_data(100)  # 你需要實現這個函數
    
    response = {
        'message': 'Initial data loaded successfully!',
        'extracted_data': initial_data
    }
    return jsonify(response)

def get_sample_data(n):
    # 實現這個函數來返回一個包含n條數據的列表
    # 可能涉及從數據庫或文件中讀取數據
    # 返回的數據格式應該與 submit_data 路由返回的格式相同
    pass

# 聯絡我們
@app.route("/contact", methods=["GET"])
def contactus():
    return render_template("contact.html")

# 登入
@app.route("/signin", methods=["GET"])
def login():
    return render_template("signin.html")

# chat bot
@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if request.method == "POST":
        if 'messages' not in session:
            session['messages'] = []

        print("Before processing: ", session['messages']) # 測試

        if request.is_json:
            data = request.get_json()
            question = data.get("question")
            response = function_call(question, session['messages'])
            session.modified = True  # 確保session更新
            print("After processing JSON: ", session['messages']) # 測試
            return jsonify({"response": response})
        else:
            message = request.form.get("message")
            response = function_call(message, session['messages'])
            session.modified = True  # 確保session更新
            return render_template("map.html", response=response)
    return render_template("chatbot.html")

# 重啟 chat bot
@app.route("/clear_session", methods=["POST"])
def clear_session():
    session.pop('messages', None)
    return '', 204

""" Line Bot """
# 監聽所有來自 /callback 的 Post Request
# @app.route("/callback", methods=['POST'])
# def callback():
#     # get X-Line-Signature header value
#     signature = request.headers['X-Line-Signature']
#     # get request body as text
#     body = request.get_data(as_text=True)
#     app.logger.info("Request body: " + body)
#     # handle webhook body
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         abort(400)
#     return 'OK'

# # 處理訊息
# @handler.add(MessageEvent, message = TextMessage)
# def handle_message(event):
#     msg = str(event.message.text)
#     if 'messages' not in session:
        # session['messages'] = []
#     # response = generate_response(msg)
#     response = function_call(msg, session['messages'])
#     line_bot_api.reply_message(event.reply_token, TextSendMessage(response))

# @handler.add(PostbackEvent)
# def handle_message(event):
#     print(event.postback.data)

# @handler.add(MemberJoinedEvent)
# def welcome(event):
#     uid = event.joined.members[0].user_id
#     gid = event.source.group_id
#     profile = line_bot_api.get_group_member_profile(gid, uid)
#     name = profile.display_name
#     message = TextSendMessage(text=f'{name}歡迎加入')
#     line_bot_api.reply_message(event.reply_token, message)


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0", port=8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)