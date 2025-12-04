from fastapi import APIRouter
import yfinance as yf

router = APIRouter()

@router.get("/ticker")
def get_ticker():
    try:
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "JPM", "V"]
        data = []
        
        # Fetch data in bulk for efficiency
        tickers = yf.Tickers(" ".join(symbols))
        
        for symbol in symbols:
            try:
                info = tickers.tickers[symbol].info
                # Use current price or previous close if market closed
                price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                previous_close = info.get("previousClose")
                
                if price and previous_close:
                    change_percent = ((price - previous_close) / previous_close) * 100
                    up = change_percent >= 0
                    change_str = f"{change_percent:+.2f}%"
                    
                    data.append({
                        "symbol": symbol.replace("-", "."), # Display BRK.B instead of BRK-B
                        "price": f"{price:.2f}",
                        "change": change_str,
                        "up": up
                    })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue
                
        return data
    except Exception as e:
        return {"error": str(e)}
