import requests
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from backend.app.chatbot.rag import get_retriever, thread_document_metadata

# 1. Initialize local tools
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=JJECYHZ7TGPXD8K7"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": f"Failed to retrieve stock quote: {str(e)}"}

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {
            "first_num": first_num,
            "second_num": second_num,
            "operation": operation,
            "result": result,
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def rag_tool(query: str, thread_id: str) -> dict:
    """
    Retrieve relevant information from the uploaded PDF for this chat thread.
    Always include the active thread_id when calling this tool.
    """
    retriever = get_retriever(thread_id)
    if retriever is None:
        return {
            "error": "No document indexed for this chat. Upload a PDF first.",
            "query": query,
        }

    try:
        result = retriever.invoke(query)
        context = [doc.page_content for doc in result]
        metadata = [doc.metadata for doc in result]
        
        # Gather all uploaded filenames for context source logging
        meta = thread_document_metadata(thread_id)
        filenames = [f["filename"] for f in meta.get("files", [])] if "files" in meta else []
        
        return {
            "query": query,
            "context": context,
            "metadata": metadata,
            "source_files": filenames,
        }
    except Exception as e:
        return {"error": f"RAG search execution failed: {str(e)}"}

def get_base_tools() -> list:
    """Return local tools list including RAG and Calculator."""
    return [search_tool, get_stock_price, calculator, rag_tool]
