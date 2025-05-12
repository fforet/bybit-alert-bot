import requests

def get_price(symbol, market):
    symbol = symbol.upper()

    if market == "현물":
        url = f"https://api.bybit.com/spot/v3/public/quote/ticker/price?symbol={symbol}"
        try:
            res = requests.get(url)
            data = res.json()
            print(f"[현물 응답] {data}")
            return float(data["result"]["price"])
        except Exception as e:
            print(f"[현물 오류] {e}")
            return None

    elif market == "선물":
        url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
        try:
            res = requests.get(url)
            data = res.json()
            print(f"[선물 응답] {data}")
            return float(data["result"][0]["last_price"])
        except Exception as e:
            print(f"[선물 오류] {e}")
            return None

# 테스트용 실행 예시
if __name__ == "__main__":
    print("▶ BTCUSDT 현물 가격:", get_price("btcusdt", "현물"))
    print("▶ BTCUSDT 선물 가격:", get_price("btcusdt", "선물"))
