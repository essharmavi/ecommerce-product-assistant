from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from prompt_lib.prompts import PROMPT_REGISTRY, PromptType

from utils.model_loader import ModelLoader
from retriever.retrieval import Retriever

model_loader = ModelLoader()
retriever_obj = Retriever()

def format_docs(docs) -> str:
    if not docs:
        return "No relevant documents found."
    
    formatted_chunks = []

    for doc in docs:
        meta = doc.metadata or {}

        formatted = (
            f"Title: {meta.get('product_title', 'N/A')}\n"
            f"Price: {meta.get('price', 'N/A')}\n"
            f"Rating: {meta.get('rating', 'N/A')}\n"
            f"Reviews:\n{doc.page_content.strip()}"
        )
        formatted_chunks.append(formatted)

    return "\n\n---\n\n".join(formatted_chunks)

def build_chain(query):
    """Build the RAG pipeline chain with retriever, prompt, LLM, and parser."""
    retriever = retriever_obj.load_retriever()
    retrieved_docs=retriever.invoke(query)

    
    retrieved_contexts = [format_docs(retrieved_docs)]
    
    llm = model_loader.load_llm()
    prompt = ChatPromptTemplate.from_template(
        PROMPT_REGISTRY[PromptType.PRODUCT_BOT].template
    )

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain,retrieved_contexts


def invoke_chain(query: str, debug: bool = False):
    """Run the chain with a user query."""
    chain,retrieved_contexts = build_chain(query)

    if debug:
        # For debugging: show docs retrieved before passing to LLM
        docs = retriever_obj.load_retriever().invoke(query)
        print("\nRetrieved Documents:")
        print(format_docs(docs))
        print("\n---\n")

    response = chain.invoke(query)
    
    return retrieved_contexts,response




