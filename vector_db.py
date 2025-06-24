from langchain_community.vectorstores import ElasticsearchStore

class VectorDb:
    def __init__(self):
        self.vectors = {}