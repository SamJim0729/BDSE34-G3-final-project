import requests
import os
import json
from dotenv import load_dotenv
import lib.recommend_house as recommend
import lib.newmortgage as mort
import lib.count_near as near

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

def get_completion(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=1000, tools=None):
  payload = { "model": model, "temperature": temperature, "messages": messages, "max_tokens": max_tokens }
  if tools:
    payload["tools"] = tools

  headers = { "Authorization": f'Bearer {openai_api_key}', "Content-Type": "application/json" }
  response = requests.post('https://api.openai.com/v1/chat/completions', headers = headers, data = json.dumps(payload) )
  obj = json.loads(response.text)

  if response.status_code == 200 :
    return obj["choices"][0]["message"] 
  else :
    return obj["error"]

available_tools = {
    "count_near": near.count_near,
    "generate_response": recommend.main,
    "mortgage_calculator": mort.calculate_loan_payments,
}

function_prompt = {
    "count_near" : """
    請陳述房屋附近多少公尺內有多少個用戶指定設施，並寫出最近的那個指定設施離房屋的距離(公尺)
    範例回答：在500公尺內有3家便利商店，最近的便利商店距離123公尺。
    """,
    "generate_response" : """ 
    依照用戶需求挑出3套適合的房產，列點呈現房產資訊並宣傳房屋優點。限制回應在200字內。

    範例回答：
    1.地址：台北市大安區杭州南路二段1巷（ID:01）\n
      總價：2188萬、預測價格：2184萬 \n
      總坪數：30坪、每坪價格：72萬/坪 \n
      優點：近幼兒園、便利商店，捷運站交通便利，為電梯大樓物件。\n
    
    2.地址：台北市中山區南京東路二段55巷（ID:03）\n
      總價：1500萬、預測價格：1498萬\n
      總坪數：25坪、每坪價格：60萬/坪\n
      優點：近超市、學校，步行可達商圈和書店，附近有健身房。\n

    3.地址：台北市松山區復興北路250巷（ID:04）\n
      總價：3500萬、預測價格：3490萬\n
      總坪數：50坪、每坪價格：70萬/坪\n
      優點：近醫院、便利商店，捷運站交通便利，周邊有高級餐廳和購物中心。\n
       """,
    "mortgage_calculator" : "請考慮用戶是否有自備款，並仔細計算出正確的貸款總額。回答用戶在總房價、還款年限等條件下，所需的總還款金額及每月還款金額，請注意單位不要寫錯",
}

def get_completion_with_function_execution(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=800, tools=None):

    response = get_completion(messages, model, temperature, max_tokens, tools)
#   print(f"get_completion response:{response}")
    messages.append(response)
  
    if isinstance(response, dict) and 'tool_calls' in response:
        for tool_call in response["tool_calls"]:
            function_name = tool_call["function"]["name"]
            id = tool_call["id"]
            function_args = json.loads(tool_call["function"]["arguments"])
            function_to_call = available_tools[function_name]
            function_response = function_to_call(**function_args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": id,
                    "name": function_name,
                    "content": str(function_response)
                }
            )
            messages.append(
                {
                    "role": "system",
                    "content": function_prompt[function_name]
                }
            )
        response = get_completion(messages, model, temperature, max_tokens)
        print(f"final response: {response}")
        messages.append(response)
    return response

def function_call(user_input, messages):
    system_input = "你是房屋智能客服，嚴禁回答問句、不相關的問題，確認回覆有完整回答用戶問題，數字單位為萬或億或元，從funtion取得的數值必須完整、正確、詳細呈現。"
    if len(messages) == 0:
        messages.append({"role": "system", "content": system_input})
    
    messages.append({"role": "user", "content": user_input})

    tools = [        
       {
            "type": "function",
            "function": {
                "name": "count_near",
                "description": "以房產為圓心，指定距離內有多少選定類別的設施",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Latitude": {
                            "type": "number",
                            "description": "緯度",
                        },
                        "Longitude": {
                            "type": "number",
                            "description": "經度",
                        },
                        "type_obj": {
                            "type": "string",
                            "description": "設施類別，請從此列表中['公共活動空間', '交流道出入口', '捷運出口', '宗教場所', '消防單位', '商圈', '圖書館', '學校', '藝文', '醫院', '加油站', '幼兒園', '托兒所', '法院_檢察署', '便利商店', '發電廠', '清潔單位', '焚化廠', '銀行', '殯儀館', '警局', '療養院', '診所', '藥局', '醫療設施']尋找",
                        },
                        "dist": {
                            "type": "number",
                            "description": "距離（公尺)",
                        }
                    },
                    "required": ["比鄰、鄰近"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_response",
                "description": "根據使用者偏好提供房屋推薦",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {
                            "type": "string",
                            "description": "keep original user_input",
                        }
                    },
                    "required": ["房屋、推薦"],
                },
            },
        },
      {
            "type": "function",
            "function": {
                "name": "mortgage_calculator",
                "description": "計算房屋貸款，若無提及利率則預設為2.18%",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Total_housing_price": {
                            "type": "integer",
                            "description": "房屋總價",
                        },
                        "Down_payment": {
                            "type": "integer",
                            "description": "自備款、現有金額",
                        },
                        "years": {
                            "type": "integer",
                            "description": "還款年限",
                        },
                        "annual_rate": {
                            "type": "number",
                            "description": "利率",
                        }
                    },
                    "required": ["貸款、房貸"],
                },
            },
        }
    ]
    
    response = get_completion_with_function_execution(messages, tools=tools)
    return response["content"]

# if __name__ == "__main__":
#     messages = []
#     user_input = "請推薦大安區2500萬交通方便的房子"
#     response = function_call(user_input,messages)
#     print(response)