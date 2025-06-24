import pandas as pd
from io import StringIO
from typing import List
from langchain_core.documents import Document

class DataLoader:
    """
    Handles loading and processing data from a source (e.g., CSV)
    and converting it into a list of LangChain Document objects.
    """
    def __init__(self, data_source: str):
        """
        Initializes the DataLoader with the source data.

        Args:
            data_source (str): A string containing the raw CSV data.
                               In a real application, this could be a file path.
        """
        self.data_source = data_source
        print("DataLoader initialized.")

    def load_and_process(self) -> List[Document]:
        """
        Loads data from the source, processes each row, and converts
        it into a LangChain Document.

        Returns:
            List[Document]: A list of documents ready for embedding.
        """
        print("Loading and processing data...")
        df = pd.read_csv(StringIO(self.data_source))
        
        documents = []
        for index, row in df.iterrows():
            # Combine relevant columns into a single text chunk for embedding
            content = (
                f"API Step: {row.get('API Step', 'N/A')}\n"
                f"Field Name: {row.get('Simple Field Name', 'N/A')}\n"
                f"Description: {row.get('Description', 'N/A')}\n"
                f"Technical Data Point: {row.get('Technical Data Point', 'N/A')}"
            )
            # Store the source API step in metadata for reference
            metadata = {"source_api_step": row.get('API Step', 'N/A')}
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
            
        print(f"Processed {len(documents)} documents.")
        return documents
