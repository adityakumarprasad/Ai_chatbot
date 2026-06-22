import requests
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

# 1. Initialize local tools
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": f"Failed to retrieve stock quote: {str(e)}"}

def get_base_tools() -> list:
    """Return local tools list."""
    return [search_tool, get_stock_price]
