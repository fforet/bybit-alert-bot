import os
import requests
import time
import threading
from flask import Flask, request

# 환경변수에서 봇 토큰과 챗 ID 가져오기
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
alarms = []
alarm_id = 1
lock = threading.Lock()

# 현물/선물 가격 가져오기
def get_price(symbol, market):
    symbol = symbol.upper()

    if market == "현물":
        url = f"https://api.bybit.com/spot/v3/public/quote/ticker/price?symbol={symbol}"
        try:
            res = requests.get(url)
            print(f"[현물 API] {url} → {res.status_code}")
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
            print(f"[선물 API] {url} → {res.status_code}")
            data = res.json()
            print(f"[선물 응답] {data}")
            return float(data["result"][0]["last_price"])
        except Exception as e:
            print(f"[선물 오류] {e}")
            return None

return None

# 텔레그램 메시지 보내기
def send_message(text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

# 알람 체크 쓰레드
def check_alarms():
    while True:
        time.sleep(10)
        with lock:
            for alarm in alarms:
                price = get_price(alarm["symbol"], alarm["market"])
                if price is None:
                    continue

                prev_price = alarm.get("prev_price")
                target = alarm["target"]

                if prev_price is not None:
                    # 목표가를 지나쳤는지 판단 (위든 아래든 통과)
                    crossed = (prev_price < target <= price) or (prev_price > target >= price)

                    if crossed:
                        last_alert = alarm.get("last_alert")
                        if last_alert is None or time.time() - last_alert > 180:
                            send_message(f"🚨 [{alarm['market']}] {alarm['symbol']} 목표가 {target} 도달! 현재가: {price}")
                            alarm["last_alert"] = time.time()

                # 이전 가격 저장
                alarm["prev_price"] = price

# 텔레그램에서 요청 처리
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    global alarm_id
    data = request.get_json()
    text = data["message"].get("text", "")

    if text.startswith("/list"):
        with lock:
            if not alarms:
                send_message("📭 현재 등록된 알람이 없습니다.")
            else:
                msg = "📋 등록된 알람 목록:\n"
                for idx, alarm in enumerate(alarms, 1):
                    msg += f"{idx}. [{alarm['market']}] {alarm['symbol']} ≥ {alarm['target']}\n"
                send_message(msg)

    elif text.startswith("/delete"):
        try:
            idx = int(text.split()[1]) - 1
            with lock:
                if 0 <= idx < len(alarms):
                    deleted = alarms.pop(idx)
                    send_message(f"❌ 알람 삭제 완료: [{deleted['market']}] {deleted['symbol']} ≥ {deleted['target']}")
                else:
                    send_message("🚫 해당 번호의 알람이 없습니다.")
        except:
            send_message("❌ 형식 오류: /delete [번호]")

    elif text.startswith("/start"):
        send_message("👋 환영합니다! 사용법: 현물|선물 심볼 목표가격\n예: 현물 btcusdt 80000")

    else:
        parts = text.split()
        if len(parts) == 3 and parts[0] in ["현물", "선물"]:
            market, symbol, target = parts
            try:
                target_price = float(target)
                with lock:
                    alarms.append({
                        "id": alarm_id,
                        "market": market,
                        "symbol": symbol.upper(),
                        "target": target_price,
                        "triggered": False,
                        "last_alert": None,
                        "prev_price": None,
                    })
                    alarm_id += 1
                    send_message(f"✅ 알람 등록 완료: [{market}] {symbol.upper()} ≥ {target_price}")
            except:
                send_message("❌ 숫자 형식 오류 : 가격은 숫자여야 합니다.")
        else:
            send_message("❓ 사용법: 현물|선물 심볼 목표가격\n예: 현물 btcusdt 80000")

    return "", 200

# 앱 실행
if __name__ == "__main__":
    t = threading.Thread(target=check_alarms)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=8443)
