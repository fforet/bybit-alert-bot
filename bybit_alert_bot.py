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

# 가격 조회 함수 (현물/선물)
def get_price(symbol, market):
    symbol = symbol.upper()
    print(f"📡 가격 요청: {market} {symbol}")

    if market == "현미":
        url = f"https://api.bybit.com/spot/v3/public/quote/ticker/price?symbol={symbol}"
    elif market == "선미":
        url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
    else:
        print("❌ 잘못된 마켓명")
        return None

    try:
        res = requests.get(url)
        print(f"🔄 API 상태: {res.status_code}")
        data = res.json()
        print(f"📦 응답: {data}")

        if market == "현미":
            return float(data["result"]["price"])
        else:
            return float(data["result"][0]["last_price"])
    except Exception as e:
        print(f"🚨 가격 채팅 오류: {e}")
        return None

# 테마그래밍 메시지 보내기
def send_message(text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

# 가격 체크 스레드

def check_alarms():
    print("✅ check_alarms() 함수 시작")
    while True:
        print("🔄 가격 확인 중...")
        time.sleep(10)
        with lock:
            for alarm in alarms:
                price = get_price(alarm["symbol"], alarm["market"])
                if price is None:
                    continue

                prev_price = alarm.get("prev_price")
                target = alarm["target"]

                if prev_price is not None:
                    crossed = (prev_price < target <= price) or (prev_price > target >= price)
                    if crossed:
                        last_alert = alarm.get("last_alert")
                        if last_alert is None or time.time() - last_alert > 180:
                            send_message(f"🚨 [{alarm['market']}] {alarm['symbol']} 목표가 {target} 도달! 현재가: {price}")
                            alarm["last_alert"] = time.time()
                alarm["prev_price"] = price

# 테마그래밍 요청 처리
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    global alarm_id
    data = request.get_json()
    text = data["message"].get("text", "")

    if text.startswith("/list"):
        with lock:
            if not alarms:
                send_message("📍 등록된 알람이 없습니다.")
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
                    send_message("🚫 해당 번호가 없습니다.")
        except:
            send_message("❌ 형식 오류: /delete [번호]")

    elif text.startswith("/start"):
        send_message("👋 환영합니다! 사용법: 현미|\uc120\ubbf8 \uc2ec\ubcfc \ubaa9\ud45c\uac00\uaca9\\n\uc608: \ud604\ubbf8 btcusdt 80000")

    else:
        parts = text.split()
        if len(parts) == 3 and parts[0] in ["현미", "선미"]:
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
            send_message("❓ 사용법: 현미|선미 심볼 목표가격\n예: 현미 btcusdt 80000")

    return "", 200

if __name__ == "__main__":
    print("✅ 메인 블록 시작")
    t = threading.Thread(target=check_alarms)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=8443)
