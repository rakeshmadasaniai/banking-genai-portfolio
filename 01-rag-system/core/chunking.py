from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents: list, chunk_size: int = 500, chunk_overlap: int = 90) -> list:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)

