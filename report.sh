#!/bin/bash
# report.sh - отправляет погоду, курсы валют и котировки акций в Telegram
# Запуск по расписанию (cron), пример через crontab -e:
# 0 9,21 * * * /home/ironcarrier/report.sh >> /home/ironcarrier/report.log 2>&1

BOT_TOKEN="8192021172:AAGloiaKYmnTEvF9j-5jeHxIavwekEnG_8k"
CHAT_ID="1165858145"

NOW=$(date '+%Y-%m-%d %H:%M:%S')

# --- Тип отчёта (передаётся из GitHub Actions, локально по умолчанию "manual") ---
REPORT_TYPE="${REPORT_TYPE:-manual}"
case "$REPORT_TYPE" in
    morning) GREETING="☀️ Доброе утро! Утренняя сводка" ;;
    lunch)   GREETING="🕐 Дневная сводка" ;;
    *)       GREETING="📋 Отчёт" ;;
esac

# --- Погода в Астане (метрическая система: °C, м/с) ---
WEATHER=$(curl -s --max-time 6 "wttr.in/Astana?format=%C+%t+(ощущается+как+%f),+ветер+%w,+влажность+%h&m" 2>/dev/null)
[ -z "$WEATHER" ] && WEATHER="нет данных"

# --- Курсы валют: USD/KZT и TRY/KZT ---
FX_JSON=$(curl -s --max-time 6 "https://open.er-api.com/v6/latest/USD" 2>/dev/null)
if [ -n "$FX_JSON" ]; then
    USD_KZT=$(echo "$FX_JSON" | grep -o '"KZT":[0-9.]*' | head -1 | cut -d: -f2)
    USD_TRY=$(echo "$FX_JSON" | grep -o '"TRY":[0-9.]*' | head -1 | cut -d: -f2)
    if [ -n "$USD_KZT" ] && [ -n "$USD_TRY" ]; then
        TRY_KZT=$(awk -v kzt="$USD_KZT" -v try="$USD_TRY" 'BEGIN{printf "%.4f", kzt/try}')
    else
        TRY_KZT="нет данных"
    fi
else
    USD_KZT="нет данных"
    TRY_KZT="нет данных"
fi
[ -z "$USD_KZT" ] && USD_KZT="нет данных"
[ -z "$TRY_KZT" ] && TRY_KZT="нет данных"

# --- Акции AIRA и HSBK с KASE ---
# Страница Angular SSR содержит сериализованный JSON.
# Ищем объект по маркеру "code":"TICKER","sec_type":"share"
# и декодируем его через json.JSONDecoder — надёжнее чем regex по полям.
fetch_kase_quote() {
    local ticker="$1"
    local page
    page=$(curl -sL --max-time 10 -A "Mozilla/5.0 (X11; Linux x86_64)" \
        "https://kase.kz/en/shares/show/${ticker}/" 2>/dev/null)
    if [ -z "$page" ]; then
        echo "нет данных"
        return
    fi
    echo "$page" | python3 -c "
import sys, json
ticker = '${ticker}'
html = sys.stdin.read()
marker = '\"code\":\"' + ticker + '\",\"sec_type\":\"share\"'
pos = html.find(marker)
if pos == -1:
    print('нет данных')
    sys.exit()
start = html.rfind('{', 0, pos)
if start == -1:
    print('нет данных')
    sys.exit()
try:
    obj, _ = json.JSONDecoder().raw_decode(html, start)
    price = obj.get('price')
    trand = obj.get('trand')
    trand_pct = obj.get('trand_percent')
    if price is None:
        print('нет данных (торги не идут)')
        sys.exit()
    price_str = str(int(price)) if price == int(price) else str(price)
    if trand is not None and trand_pct is not None:
        sign = '+' if trand >= 0 else ''
        sign_pct = '+' if trand_pct >= 0 else ''
        print(f'{price_str} KZT ({sign}{trand:.2f}, {sign_pct}{trand_pct:.2f}%)')
    else:
        print(f'{price_str} KZT')
except Exception:
    print('нет данных')
"
}

AIRA_PRICE=$(fetch_kase_quote "AIRA")
HSBK_PRICE=$(fetch_kase_quote "HSBK")

MSG="${GREETING}
${NOW}
🌤 Погода в Астане:
  ${WEATHER}
💵 Курсы валют:
  USD/KZT: ${USD_KZT}
  TRY/KZT: ${TRY_KZT}
📈 Акции (KASE):
  AIRA (Air Astana): ${AIRA_PRICE}
  HSBK (Halyk Bank): ${HSBK_PRICE}"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  --data-urlencode chat_id="${CHAT_ID}" \
  --data-urlencode text="${MSG}" > /dev/null

echo "Отчёт (${REPORT_TYPE}) отправлен: ${NOW}"
