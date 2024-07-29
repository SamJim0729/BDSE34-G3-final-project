import requests
import os
import json
import random
from dotenv import load_dotenv
import tiktoken
import lib.recommend_house as recommend
import lib.newmortgage as mort
import time
import lib.count_near as near

start_time = time.time()
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

def count_tokens(messages, model_name="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            num_tokens += len(encoding.encode(content))
        # else:
        #     print(f"Warning: Skipping non-string content: {content}")
    return num_tokens

def get_completion(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=1000, tools=None):
    input_token_count = count_tokens(messages, model)
    # print(f"Input Tokens (before request): {input_token_count}") 

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
        "max_tokens": max_tokens
    }
    if tools:
        payload["tools"] = tools

    headers = {
        "Authorization": f'Bearer {openai_api_key}',
        "Content-Type": "application/json"
    }
    
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(payload))
    obj = json.loads(response.text)

    # print(f"API Response: {json.dumps(obj, indent=2)}")  

    if response.status_code == 200:
        usage = obj.get("usage", {})
        output_token_count = usage.get("completion_tokens", 0)
        prompt_token_count = usage.get("prompt_tokens", 0)
        total_token_count = usage.get("total_tokens", 0)
        if 'choices' in obj and len(obj['choices']) > 0:
            return obj["choices"][0]["message"], input_token_count, prompt_token_count, output_token_count, total_token_count
        else:
            print("Warning: No choices found in API response.")
            return "No response generated", input_token_count, prompt_token_count, 0, input_token_count
    else:
        return obj["error"], input_token_count, 0, 0, input_token_count

available_tools = {
    "count_near": near.count_near,
    "generate_response": recommend.main,
    "mortgage_calculator": mort.calculate_loan_payments,
}
function_prompt = {
    "count_near" : "請陳述房屋附近的定義（公尺）有多少個用戶指定設施，並寫出最近的那個指定設施離房屋的距離(公尺)",
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
    "mortgage_calculator" : "請考慮用戶是否有自備款，並仔細計算出正確的貸款總額。回答用戶在總房價、還款年限等條件下，所需的總還款金額及每月還款金額",
}

def get_completion_with_function_execution(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=800, tools=None):
    # print(f"messages: {messages}")
    response, input_tokens, prompt_tokens, output_tokens, total_tokens = get_completion(messages, model, temperature, max_tokens, tools)
    # print(f"response: {response}")
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
        # print(f"final messages: {messages}")
        response, input_tokens, prompt_tokens, output_tokens, total_tokens = get_completion(messages, model, temperature, max_tokens)
        print(f"final response: {response}")
        messages.append(response)
    
    return response, input_tokens, prompt_tokens, output_tokens, total_tokens

def function_call(user_input, messages):
    random_number = random.randint(0, 4)
    personality_list=[
        "用恭敬的態度回答用戶問題",
        "用開心開朗的態度回答用戶問題",
        "用悲觀的態度回答用戶問題",
        "用不奈煩的態度回答用戶問題",
        "用冷漠的態度回答用戶問題",
    ]
    system_input = "你是房屋智能客服，嚴禁回答問句、不相關的問題，確認回覆有完整回答用戶問題，數字單位為萬或元，從funtion取得的數值必須完整、正確、詳細呈現。"
    system_input = personality_list[random_number] + system_input
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
                            "description": "設施類別",
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
    
    response, input_tokens, prompt_tokens, output_tokens, total_tokens = get_completion_with_function_execution(messages, tools=tools)
    return response, input_tokens, prompt_tokens, output_tokens, total_tokens

if __name__ == "__main__":
    messages = []
    # user_input ="第一間自備款200萬，貸款三十年"
    # user_input = "第三間房1.5公里內有商圈嗎？"
    user_input = "台北內湖區2000萬以下交通方便的房子"
    response, input_tokens, prompt_tokens, output_tokens, total_tokens = function_call(user_input, messages)
    # print("Input Tokens:", input_tokens)
    # print("Prompt Tokens:", prompt_tokens)
    # print("Output Tokens:", output_tokens)
    total_cost = (((input_tokens + prompt_tokens + 453 ) * 0.5 + output_tokens* 1.5) * 32.52 / 1000000)
    print("total cost: {:.4f}元".format(total_cost))
    end_time = time.time()
execution_time = end_time - start_time
print(f"程式執行時間：{execution_time:.2f}秒")

#房貸：0.03元/ 4秒
#推薦：0.05-0.09元/19秒

