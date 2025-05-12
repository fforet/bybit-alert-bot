def get_price(symbol, market):
    import requests
    symbol = symbol.upper()
    headers = {"User-Agent": "Mozilla/5.0"}

    if market == "현물":
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
        try:
            res = requests.get(url, headers=headers)
            data = res.json()
            print(f"[현물 응답] {data}")
            return float(data["result"]["list"][0]["lastPrice"])
        except Exception as e:
            print(f"[현물 오류] {e}")
            return None

    elif market == "선물":
        url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
        try:
            res = requests.get(url, headers=headers)
            data = res.json()
            print(f"[선물 응답] {data}")
            return float(data["result"][0]["last_price"])
        except Exception as e:
            print(f"[선물 오류] {e}")
            return None
