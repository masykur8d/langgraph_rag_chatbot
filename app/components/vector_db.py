import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List

import pandas as pd
from upstash_vector import Index

from langchain_community.vectorstores.upstash import UpstashVectorStore
from langchain.docstore.document import Document


# Set Japan timezone
japan_tz = ZoneInfo("Asia/Tokyo")


def get_vector_store(namespace : str) -> UpstashVectorStore:
    vector_store = UpstashVectorStore(
        embedding=True,
        namespace=namespace,
    )

    return vector_store


def get_specific_vector_data(namespace: str, list_id: List[str]) -> pd.DataFrame:
    index = Index.from_env()
    
    responses = index.fetch(
        ids=list_id,
        namespace=namespace,
        include_vectors=False,
        include_metadata=True,
        include_data=True
    )

    all_vectors_metadata = []
    for res in responses:
        vector_id = res.id
        metadata = res.metadata
        metadata['vector_id'] = vector_id

        all_vectors_metadata.append(metadata)
    
    df_specific_vector = pd.DataFrame(all_vectors_metadata)

    return df_specific_vector


def get_vector_data(namespace: str) -> pd.DataFrame:
    index = Index.from_env()
    all_vectors_metadata = []
    cursor = ''  # Start with an empty cursor

    while True:
        res = index.range(
            namespace=namespace,
            cursor=cursor,
            limit=100,
            include_vectors=False,
            include_metadata=True,
            include_data=True,
        )

        for vector in res.vectors:
            vector_id = vector.id
            vector_metadata = vector.metadata
            vector_metadata['vector_id'] = vector_id

            all_vectors_metadata.append(vector_metadata)

        time.sleep(0.5)

        if res.next_cursor == "":
            break

        cursor = res.next_cursor

    df_namespace_data = pd.DataFrame(all_vectors_metadata)
    return df_namespace_data


def create_document(page_content : str, metadata : dict) ->Document:
    doc = Document(
        page_content = page_content,
        metadata = metadata
    )

    return doc


def add_vector_data(namespace: str, qa_text: str, service: str) -> List[str]:
    local_date = datetime.now(japan_tz).strftime("%Y/%m/%d")
    local_time = datetime.now(japan_tz).strftime("%H:%M:%S")

    doc = create_document(
        page_content = qa_text,
        metadata = {
            "service" : service,
            "chat_bot_type" : "q_and_a",
            "added_date" : local_date,
            "added_time" : local_time,
        } 
    )

    store = get_vector_store(namespace=namespace)
    list_added_id = store.add_documents(documents=[doc])

    return list_added_id


def remove_vector(vector_ids: List[str], namespace: str) -> bool:
    index = Index.from_env()

    res = index.delete(
        ids=vector_ids,
        namespace=namespace,
    )

    all_deleted = len(vector_ids) == res.deleted

    return all_deleted

# import os
# from langchain.docstore.document import Document

# # Load environtment variables
# from dotenv import load_dotenv
# env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
# load_dotenv(dotenv_path=env_path, override=True)

# def create_document(page_content : str, metadata : dict) ->Document:
#     doc = Document(
#         page_content = page_content,
#         metadata = metadata
#     )

#     return doc

# def upsert_vector(docs : list[Document]) -> None:
#     store = get_vector_store('saitama-omiya-shaken')
#     store.add_documents(documents=docs)


# from datetime import datetime
# from zoneinfo import ZoneInfo

# # Set Japan timezone
# japan_tz = ZoneInfo("Asia/Tokyo")

# local_date = datetime.now(japan_tz).strftime("%Y/%m/%d")
# local_time = datetime.now(japan_tz).strftime("%H:%M:%S")

# page_contents = [
#     "車検を受けようか迷っているのですが、相談だけでも可能でしょうか？はい、もちろん可能でございます。車検についてお悩みでしたら、お気軽にご連絡ください。",
#     "車検の見積もりは、本当に無料ですか？はい。当店では、お見積もりは無料で承っております。お車の状態によっては、車検当日に追加整備が必要となる可能性もありますので、まずはお気軽にお問い合わせください。",
#     "車検の時間はどれくらいかかりますか？車検の時間は、お車の種類や状態によっても異なりますが、大体1時間～3時間程度で完了いたします。具体的な時間については、車検のご予約時にお伝えいたします。",
#     "車検はいつから受けられますか？車検満了日の1ヶ月前から受けることが可能でございます。車検を受ける際は、車検証などの必要書類をお持ちください。",
#     "車検には何が必要ですか？車検証、自賠責保険証、納税証明書、印鑑、車検費用が必要となります。",
#     "車検の支払いは何が利用できますか？	現金、各種クレジットカード、各種ローンがご利用いただけます。",
#     "車検で車を預ける際に、代車はありますか？はい、代車は無料でご用意しております。車検の間、代車が必要な場合は、ご予約時にお申し付けください。",
#     "車検ではどこを点検・整備するのですか？道路運送車両法の保安基準に基づき、国が定める点検項目を点検・整備いたします。具体的な点検項目については、車検のご予約時にお伝えいたします。",
#     "外車・輸入車も車検できますか？はい、当店では輸入車や外車であっても、車検ができます。輸入車や外車の場合、部品の取り寄せなどで時間がかかる場合がありますので、早めのご予約をおすすめいたします。",
#     "車検を受けられるか、車を見て欲しいのですが？はい、当店ではお車の状態を確認させていただき、車検を受けられるかどうか判断いたします。まずはお気軽にお問い合わせください。",
#     "改造車ですが、車検は受けられますか？車の状態によっては、車検を受けられない場合もあります。まずはお気軽にお問い合わせください。",
#     "エンジンオイルはどれくらいの頻度で交換するのですか？お車の種類や状態によっても異なりますが、3000km～5000kmまたは3ヶ月～6ヶ月のどちらか早いタイミングで交換することをおすすめいたします。",
#     "車検が切れてしまいました。どうすれば良いですか？車検切れの車を公道で走らせると「無車検運行」として、道路運送車両法違反で罰則が科せられます。そのため、車検切れとなった際は、当店にご相談ください。",
#     "車の調子が悪いのですが、どうすれば良いですか？車の調子が悪いと感じたら、まずは当店にご相談ください。当店では、お車の状態を確認させていただき、適切な対処法をご提案いたします。",
#     "土日や祝日でも車検は受けられますか？はい、当店では土日祝日でも車検を受け付けております。お気軽にご予約ください。",
#     "車検と法定点検の違いは何ですか？車検は、国が定める保安基準に適合しているか確認する検査です。法定点検は、安全の確保及び公害防止のために、車の故障を未然に防ぎ、その機能を維持するために定期的に行う点検です。",
#     "法定12ヶ月点検は、いくらかかりますか？	車のサイズによって料金が異なります。軽自動車は9680円、小型乗用車(～1,000kg)は11,880円、中型乗用車(1,001kg～1,500kg)は13,200円、大型乗用車(1,501kg～)は14,300円となっております。",
# ]
# list_documents = []
# for i in page_contents:
#     doc = create_document(
#         page_content = i,
#         metadata = {
#             "service" : "車検",
#             "chat_bot_type" : "q_and_a",
#             "added_date" : local_date,
#             "added_time" : local_time,
#         } 
#     )
#     list_documents.append(doc)

# upsert_vector(docs=list_documents)