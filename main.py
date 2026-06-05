"""
==============================================================
  Ежедневная сводка → Telegram
  Запуск: GitHub Actions (бесплатно, 24/7)
==============================================================
"""

import os
import sys
import requests
from datetime import datetime

# ==============================================================
#  ⚙️  НАСТРОЙКИ
# ==============================================================

TELEGRAM_TOKEN      = "8192021172:AAGloiaKYmnTEvF9j-5jeHxIavwekEnG_8k"
TELEGRAM_CHAT_ID    = "1165858145"
OPENWEATHER_API_KEY = "58e08edbba6a3ee4cb4cb3b3a1e3535d"
NEWS_API_KEY        = "3d3896a14f4a4338ab870c268b927220"

REPORT_TYPE = os.environ.get("REPORT_TYPE", "morning")
CITY        = "Astana"


# ==============================================================
#  📤  ОТПРАВКА В TELEGRAM
# ==============================================================

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
    }
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code == 200:
        print("✅ Отправлено в Telegram")
    else:
        print(f"❌ Ошибка: {r.status_code} — {r.text}")
        sys.exit(1)


# ==============================================================
#  🌤  ПОГОДА
# ==============================================================

def get_weather() -> str:
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
        )
        d        = requests.get(url, timeout=10).json()
        temp     = round(d["main"]["temp"])
        feels    = round(d["main"]["feels_like"])
        desc     = d["weather"][0]["description"].capitalize()
        humidity = d["main"]["humidity"]
        wind     = round(d["wind"]["speed"])
        return (
            f"🌤 <b>Погода в Астане</b>\n"
            f"{desc}, {temp}°C (ощущается {feels}°C)\n"
            f"Влажность: {humidity}% | Ветер: {wind} м/с"
        )
    except Exception as e:
        return f"🌤 Погода: не удалось получить данные ({e})"


# ==============================================================
#  📰  НОВОСТИ
# ==============================================================

def get_news(count: int = 3) -> str:
    try:
        url = (
            f"https://newsapi.org/v2/top-headlines"
            f"?country=kz&apiKey={NEWS_API_KEY}&pageSize={count}"
        )
        articles = requests.get(url, timeout=10).json().get("articles", [])

        if not articles:
            url = (
                f"https://newsapi.org/v2/top-headlines"
                f"?language=ru&apiKey={NEWS_API_KEY}&pageSize={count}"
            )
            articles = requests.get(url, timeout=10).json().get("articles", [])

        lines = ["📰 <b>Главные новости</b>"]
        for i, a in enumerate(articles[:count], 1):
            title = a.get("title", "—").split(" - ")[0]
            lines.append(f"{i}. {title}")
        return "\n".join(lines)
    except Exception as e:
        return f"📰 Новости: не удалось получить данные ({e})"


# ==============================================================
#  💱  КУРСЫ ВАЛЮТ
# ==============================================================

def get_currency() -> str:
    try:
        url   = "https://api.exchangerate-api.com/v4/latest/KZT"
        rates = requests.get(url, timeout=10).json().get("rates", {})
        usd   = round(1 / rates["USD"], 2)
        try_  = round(1 / rates["TRY"], 2)
        return (
            f"💱 <b>Курсы валют</b>\n"
            f"USD/KZT: <code>{usd} ₸</code>\n"
            f"TRY/KZT: <code>{try_} ₸</code>"
        )
    except Exception as e:
        return f"💱 Курсы: не удалось получить данные ({e})"


# ==============================================================
#  📈  АКЦИИ
# ==============================================================

def get_stocks() -> str:
    try:
        import yfinance as yf
        tickers = {
            "Народный Банк (HSBK)": "HSBK.IL",
            "Air Astana (AIRA)":    "AIRA.IL",
        }
        lines = ["📈 <b>Котировки акций</b>"]
        for name, sym in tickers.items():
            try:
                hist = yf.Ticker(sym).history(period="1d")
                if not hist.empty:
                    price = round(hist["Close"].iloc[-1], 2)
                    prev  = round(hist["Open"].iloc[-1], 2)
                    diff  = round(price - prev, 2)
                    arrow = "🟢" if diff >= 0 else "🔴"
                    sign  = "+" if diff >= 0 else ""
                    lines.append(f"{arrow} {name}: <code>{price}</code> ({sign}{diff})")
                else:
                    lines.append(f"⚪ {name}: нет данных")
            except:
                lines.append(f"⚪ {name}: нет данных")
        return "\n".join(lines)
    except ImportError:
        return "📈 Акции: yfinance не установлен"


# ==============================================================
#  📋  ОТЧЁТЫ
# ==============================================================

def morning_report():
    date = datetime.now().strftime("%d.%m.%Y")
    parts = [
        f"☀️ <b>Доброе утро! {date}</b>\n",
        get_weather(),
        "",
        get_news(3),
        "",
        "<i>Хорошего дня!</i>"
    ]
    send_telegram("\n".join(parts))


def lunch_report():
    date = datetime.now().strftime("%d.%m.%Y")
    parts = [
        f"📊 <b>Дневная сводка {date}</b>\n",
        get_currency(),
        "",
        get_stocks(),
        "",
        get_news(3),
    ]
    send_telegram("\n".join(parts))


# ==============================================================
#  🚀  ЗАПУСК
# ==============================================================

if __name__ == "__main__":
    print(f"▶ Тип отчёта: {REPORT_TYPE}")
    if REPORT_TYPE == "morning":
        morning_report()
    elif REPORT_TYPE == "lunch":
        lunch_report()
    else:
        print(f"❌ Неизвестный тип: {REPORT_TYPE}")
        sys.exit(1)
