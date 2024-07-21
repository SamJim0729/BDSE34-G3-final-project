import json
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

#記得在製作.env 並在其中寫入 PINECONE_API_KEY= ,若不行再加上 PINECONE_ENV=us-east-1
load_dotenv()

index_name = "1024"

#Embeddings方法
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3") #1024維

def ensure_list_not_null(value):
    return value if value != '不詳' else []

docs = []
with open('data/final_predicted$.json', 'r', encoding='utf-8') as f:
    property_data = json.load(f)

for i, property in enumerate(property_data):
    for key, value in property.items():
        if value is None:
            property[key] = "不詳"

    property['售價總價'] = int(property['售價總價'])
    property['總售價差異'] = int(property['總售價差異'][:-1])

    bedrooms = property["bedrooms"]
    if bedrooms != "不詳":
        bedrooms = int(bedrooms)

    living_rooms = property["living_rooms"]
    if living_rooms != "不詳":
        living_rooms = int(living_rooms)

    total_floors = property["total_floors"]
    if total_floors != "不詳":
        total_floors = int(total_floors)
    
    target_floors = property["target_floors"]
    if target_floors != "不詳":
        target_floors = int(target_floors)

    a = property["公設比"]
    if a != "不詳":
       a *= 100
       a = str(int(a)) + "%"

    
    description = (
        f"格局: {bedrooms}房{living_rooms}廳, 屋齡: {property.get('屋齡')},"
        f"權狀坪數: {property.get('權狀坪數')}, 樓層: 在{total_floors}層中第{target_floors}層,"
        f"型態: {property.get('型態')},法定用途: {property.get('法定用途')},"
        f"車位: {property.get('車位')}, 公設比: {a},"
        f"生活機能: {', '.join(ensure_list_not_null(property.get('生活機能', [])))}, 附近交通: {ensure_list_not_null(property.get('附近交通', []))}"
    )
    print(description)
    property["index"] = i
    # print(property)
    docs.append(Document(
        page_content=description,
        metadata=property
    ))

# 上傳資料
vectors_from_doc = PineconeVectorStore.from_documents(
    docs,
    index_name = index_name,
    embedding = embeddings
)