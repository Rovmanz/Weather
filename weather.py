import sys
import requests
from datetime import datetime

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: ("☀️", "Ясно"),
    1: ("🌤️", "Преимущественно ясно"),
    2: ("⛅", "Переменная облачность"),
    3: ("☁️", "Пасмурно"),
    45: ("🌫️", "Туман"),
    48: ("🌫️", "Изморозь"),
    51: ("🌦️", "Слабая морось"),
    53: ("🌦️", "Морось"),
    55: ("🌧️", "Сильная морось"),
    56: ("🌧️", "Ледяная морось"),
    57: ("🌧️", "Сильная ледяная морось"),
    61: ("🌧️", "Небольшой дождь"),
    63: ("🌧️", "Дождь"),
    65: ("🌧️", "Сильный дождь"),
    66: ("🌨️", "Ледяной дождь"),
    67: ("🌨️", "Сильный ледяной дождь"),
    71: ("🌨️", "Небольшой снег"),
    73: ("❄️", "Снег"),
    75: ("❄️", "Сильный снег"),
    77: ("🌨️", "Снежная крупа"),
    80: ("🌦️", "Небольшие ливни"),
    81: ("🌧️", "Ливни"),
    82: ("⛈️", "Сильные ливни"),
    85: ("🌨️", "Небольшой снегопад"),
    86: ("❄️", "Сильный снегопад"),
    95: ("⛈️", "Гроза"),
    96: ("⛈️", "Гроза с градом"),
    99: ("⛈️", "Сильная гроза с градом"),
}

WEEKDAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
MONTHS_RU = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
             "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def get_weather_icon(code):
    return WEATHER_CODES.get(code, ("❓", "Неизвестно"))


def get_coordinates(city_name):
    params = {"name": city_name, "count": 1, "language": "ru", "format": "json"}
    r = requests.get(GEOCODE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if "results" not in data or not data["results"]:
        return None
    res = data["results"][0]
    return {
        "lat": res["latitude"],
        "lon": res["longitude"],
        "name": res["name"],
        "country": res.get("country", ""),
    }


def fetch_forecast(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,weathercode",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": 16,
    }
    r = requests.get(FORECAST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def format_date_ru(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = WEEKDAYS_RU[dt.weekday()]
    return f"{dt.day} {MONTHS_RU[dt.month]} ({weekday})"


def show_day(data, location):
    today = data["daily"]["time"][0]
    print(f"\n📍 {location['name']}, {location['country']}")
    print(f"📅 Погода на сегодня — {format_date_ru(today)}\n")

    hours = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    codes = data["hourly"]["weathercode"]

    for i in range(len(hours)):
        if not hours[i].startswith(today):
            continue
        hour = hours[i][11:16]
        emoji, desc = get_weather_icon(codes[i])
        print(f"  {hour}  {emoji}  {temps[i]:>5.1f}°C   {desc}")


def show_week(data, location):
    print(f"\n📍 {location['name']}, {location['country']}")
    print("📅 Погода на неделю\n")

    days = data["daily"]["time"][:7]
    codes = data["daily"]["weathercode"][:7]
    tmax = data["daily"]["temperature_2m_max"][:7]
    tmin = data["daily"]["temperature_2m_min"][:7]

    for i in range(len(days)):
        emoji, desc = get_weather_icon(codes[i])
        date_label = format_date_ru(days[i])
        print(f"  {date_label:<28} {emoji}  {tmin[i]:>5.1f}°C / {tmax[i]:>5.1f}°C   {desc}")


def show_month(data, location):
    print(f"\n📍 {location['name']}, {location['country']}")
    print("📅 Погода на ближайшие дни (доступно до 16 дней вперёд)\n")

    days = data["daily"]["time"]
    codes = data["daily"]["weathercode"]
    tmax = data["daily"]["temperature_2m_max"]
    tmin = data["daily"]["temperature_2m_min"]

    for i in range(len(days)):
        emoji, desc = get_weather_icon(codes[i])
        date_label = format_date_ru(days[i])
        print(f"  {date_label:<28} {emoji}  {tmin[i]:>5.1f}°C / {tmax[i]:>5.1f}°C   {desc}")


def main():
    print("=" * 50)
    print("       🌦️  ПРОГНОЗ ПОГОДЫ  🌦️")
    print("=" * 50)

    city = input("\nВведите город: ").strip()
    if not city:
        print("Город не указан.")
        sys.exit(1)

    try:
        location = get_coordinates(city)
    except requests.RequestException as e:
        print(f"Ошибка запроса геокодера: {e}")
        sys.exit(1)

    if location is None:
        print("Город не найден. Проверьте написание.")
        sys.exit(1)

    print("\nВыберите период:")
    print("  1 — День (почасово)")
    print("  2 — Неделя (7 дней)")
    print("  3 — Месяц (доступный прогноз)")
    choice = input("Ваш выбор (1/2/3): ").strip()

    try:
        data = fetch_forecast(location["lat"], location["lon"])
    except requests.RequestException as e:
        print(f"Ошибка запроса прогноза: {e}")
        sys.exit(1)

    if choice == "1":
        show_day(data, location)
    elif choice == "2":
        show_week(data, location)
    elif choice == "3":
        show_month(data, location)
    else:
        print("Неверный выбор.")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()
