from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts.prompt import PromptTemplate

class StringListLoader(BaseLoader):

    def __init__(self, list_of_strings):
        self.list_of_strings = list_of_strings

    def load(self):
        metadata = []
        docs = []
        for idx, s in enumerate(self.list_of_strings):
            metadata = {"source": idx}
            page_content = s
            docs.append(Document(page_content=page_content, metadata=metadata))
        return docs
    
class RetrievalShoppingLLM:
    """When using, try to pack as much context into the strs_to_search as possible, so like brand, category, description, etc."""

    def __init__(self, strs_to_search):
        open_ai_embeddings = OpenAIEmbeddings()
        data_loader = StringListLoader(strs_to_search)
        langchain_docs_data = data_loader.load()
        chroma_docs_retriever = Chroma.from_documents(langchain_docs_data, open_ai_embeddings)

        self.retrieval_query_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(), 
            chain_type="stuff", 
            retriever=chroma_docs_retriever.as_retriever(), 
            return_source_documents=True
        )


    def get_output(self, user_input):
        output = self.retrieval_query_chain({"query": user_input})
        return {
            "raw_results": output["result"],
            "source_documents": output["source_documents"],
            "raw_output": output
        }


class RetrievalShoppingLLMTemplated:

    def __init__(self, strs_to_search):
        open_ai_embeddings = OpenAIEmbeddings()
        data_loader = StringListLoader(strs_to_search)
        langchain_docs_data = data_loader.load()
        chroma_docs_retriever = Chroma.from_documents(langchain_docs_data, open_ai_embeddings)

        prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

        {context}

        Question: {question}
        Answer:"""

        retrieval_prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        chain_type_kwargs = {"prompt": retrieval_prompt}

        self.retrieval_query_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(), 
            chain_type="stuff", 
            retriever=chroma_docs_retriever.as_retriever(), 
            return_source_documents=True,
            chain_type_kwargs=chain_type_kwargs
        )


    def get_output(self, user_input):
        output = self.retrieval_query_chain({"query": user_input})
        return {
            "raw_results": output["result"],
            "source_documents": output["source_documents"],
            "raw_output": output
        }
