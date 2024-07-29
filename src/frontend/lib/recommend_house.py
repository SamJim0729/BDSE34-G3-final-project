#用langChain的方法查詢
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
import json
import os
import requests

load_dotenv()
# 從環境變量中獲取API密鑰
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

#pinecone資料庫名稱
index_name = "1024"

#Embeddings方法
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3") #1024維
vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)

def get_completion(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=1000,format_type=None):
    payload = { "model": model, "temperature": temperature, "messages": messages, "max_tokens": max_tokens }
    if format_type:
        payload["response_format"] =  { "type": format_type }
    headers = { "Authorization": f'Bearer {openai_api_key}', "Content-Type": "application/json" }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers = headers, data = json.dumps(payload) )
    obj = json.loads(response.text)
    if response.status_code == 200 :
        return obj["choices"][0]["message"]["content"]
    else :
        return obj["error"]

def extract_keyword(user_input):
    prompt = f"""
        從以下的房產查詢描述中提取關於價錢、縣市、行政區的關鍵字，並將其他主題的關鍵字或形容詞分開列出，並整理成json格式給我：

        範例1:
        描述:新北板橋區便宜套房，有電梯，新一點
        價錢關鍵字: 1000
        縣市關鍵字：新北市
        行政區關鍵字: 板橋區
        其他關鍵字: 便宜套房, 有電梯, 新

        限制：
        縣市關鍵字：台北市、新北市二選一。
        行政區關鍵字：必須是新北或是台北的行政區， 一定要加上區這個字。
        價錢關鍵字：單位為萬，必須符合INT格式，為純整數數字。
        

        現在請提取以下描述中的關鍵字：
        描述: {user_input}
        價錢關鍵字:
        縣市關鍵字:
        行政區關鍵字:
        其他關鍵字:
       """
    messages=[
                {"role": "system", "content": "你是一個能夠從用戶輸入中把價錢、縣市、行政區的關鍵字取出，其他關鍵字分為另一類的助手。"},
                {"role": "user", "content": prompt},
            ]
    result1 = get_completion(messages,format_type='json_object')
    result = json.loads(result1)
    price = result.get("價錢關鍵字", "180000")
    city = result.get("縣市關鍵字", "無")
    district = result.get("行政區關鍵字", "無")
    other = result.get("其他關鍵字", "無")

    return price, city, district, other

#問題轉成向量搜尋(5筆)
def pinecone_search(price, city, district, other, vectorstore):
    query = ' '.join(other)  # 將列表轉換為字符串
    filter = {}
    citys = ["台北市","新北市"]
    districts= ["松山區","信義區","大安區","中山區","中正區","大同區","萬華區","文山區","南港區","內湖區","士林區","北投區","板橋區","三重區","中和區","永和區","新莊區","新店區","土城區","蘆洲區","樹林區","淡水區","汐止區","三峽區","瑞芳區","五股區","泰山區","林口區","深坑區","石碇區","坪林區","三芝區","石門區","八里區","平溪區","萬里區","烏來區","雙溪區","貢寮區","金山區","鶯歌區"
    ]
    if not price:
        filter["售價總價"] = {"$lt": 18000}
    else:
        filter["售價總價"] = {"$lt": price}
    if city is not None:
        filter["縣市"] = {"$eq": city}
    if district is not None:
        filter["地區"] = {"$eq": district}
    print(filter)
    response=vectorstore.similarity_search(query,k=5,filter=filter)
    return response

def format_properties(response):
    formatted_list = []
    for doc in response:
        metadata = doc.metadata
        formatted_list.append(f"售價: {int(metadata['售價總價'])}萬, 預測價格: {int(metadata['模型_實際價格'])}萬, 地址: {metadata['地址']}, 生活機能: {metadata.get('生活機能', '無')}, 型態: {metadata.get('型態', '無')}, 交通: {metadata.get('附近交通', '無')}, 緯度: {metadata.get('latitude', '無')}, 經度: {metadata.get('longtitude', '無')},Index: {int(metadata['index'])},總坪數:{int(metadata.get('權狀坪數', '無'))},每坪售價:{int(metadata.get('每坪售價', '無'))}")
    return "\n".join(formatted_list)


def generate_response(user_input, formatted_response):

    prompt = f"""
    用戶的查詢描述: {user_input}

    以下是幾個符合用戶查詢的房產信息：

    請仔細閱讀用戶的查詢描述，印出{user_input}接著在{formatted_response}中，依照用戶需求挑出三套適合的房產，列點呈現房產資訊(總價、預測價格、地址、經度、緯度、index=ID)及宣傳房屋優點。限制回應在300字內。

    若{formatted_response}為空值則回覆:牙咧牙咧~超出查詢範圍(僅限雙北)啦，你這小淘氣

    範例回答：
    1. 地址：台北市大安區杭州南路二段1巷（ID:01）\n
       總價：2188萬、預測價格：2184萬。\n
       經度：121.5060766, 緯度：25.0284745\n

    2. 地址：台北市大安區敦化南路7巷（ID:13）\n
       總價：1980萬、預測價格：1435萬。\n
       經度：121.5122784, 緯度：25.0457644\n

    3. 地址：台北市大安區杭州南路二段6巷（ID:88）\n
       總價：1778萬、預測價格：1348萬。\n
       經度：121.5122784, 緯度：25.0457644\n
    """

    response = get_completion([{ "role": "user", "content": prompt }], temperature=0)
    return response


def main(user_input):
    price, city, district, other = extract_keyword(user_input)
    print(f"price:{price}, city:{city}, district:{district}, other:{other}")
    pinecone_search_result = pinecone_search(price, city, district, other, vectorstore)
    # print(pinecone_search_result)
    formatted_response = format_properties(pinecone_search_result)
    # print(formatted_response) 
    # response = generate_response(user_input, formatted_response)

    return formatted_response

if __name__ == "__main__":
    #用戶問題
    user_input = "新北林口便宜附近有電影院、商圈的房子"
    response = main(user_input)
    print("end:"+response)