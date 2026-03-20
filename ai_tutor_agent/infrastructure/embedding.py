import dashscope
from http import HTTPStatus

class QwenEmbedding:
    def __init__(self, api_key: str):
        dashscope.api_key = api_key

    def get_embeddings(self, texts: list[str]):
        resp = dashscope.TextEmbedding.call(
            model=dashscope.TextEmbedding.Models.text_embedding_v2,
            input=texts
        )
        if resp.status_code == HTTPStatus.OK:
            return [item['embedding'] for item in resp.output['embeddings']]
        else:
            raise Exception(f"Embedding failed: {resp.message}")