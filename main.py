from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal
import swisseph as swe
import datetime
import os
from functools import lru_cache

app = FastAPI()
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Подключение точных файлов эфемерид (скачанных в Docker)
swe.set_ephe_path(os.getenv("SWISSEPH_PATH", "/app/ephe"))

# Планеты (Плутон исключен согласно стр. 151 методички ИППН)
SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE = 0, 1, 2, 3, 4, 5, 6, 7, 8
PLANETS = [SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE]
FAST_PLANETS = {SUN, MOON, MERCURY, VENUS, MARS}

# ТОЧНЫЕ ОРБИСЫ ИППН (стр. 186 / PDF стр. 38)
ASPECTS = {
    0: 5.0,   # Соединение (±5°)
    30: 1.0,  # Семисекстиль (±1°)
    45: 1.0,  # Семиквинтиль (±1°)
    60: 3.0,  # Секстиль (±3°)
    90: 3.0,  # Квадратура (±3°)
    120: 3.0, # Тригон (±3°)
    135: 1.0, # Сесквиквадрат (±1°)
    150: 1.0, # Квинкункс (±1°)
    180: 3.0  # Оппозиция (±3°)
}

# ПОЛНАЯ ОЦИФРОВКА ТАБЛИЦЫ 1 (стр. 44)
TABLE_1 = {
    (SUN, MERCURY): {0: 21200},
    (SUN, VENUS): {0: 77000},
    (SUN, MOON): {0: 3870000, 30: 44, 45: -44, 60: 1968, 90: -1968, 120: 1968, 135: -44, 150: -44, 180: -3870000},
    (SUN, MARS): {0: 21200, 30: 12, 45: -12, 60: 145, 90: -145, 120: 145, 135: -12, 150: -12, 180: -21200},
    (SUN, JUPITER): {0: 300000, 30: 24, 45: -24, 60: 548, 90: -548, 120: 548, 135: -24, 150: -24, 180: -300000},
    (SUN, SATURN): {0: 95000, 30: 18, 45: -18, 60: 308, 90: -308, 120: 308, 135: -18, 150: -18, 180: -95000},
    (SUN, URANUS): {0: 17000, 30: 11, 45: -11, 60: 130, 90: -130, 120: 130, 135: -11, 150: -11, 180: -17000},
    (SUN, NEPTUNE): {0: 12000, 30: 10, 45: -10, 60: 110, 90: -110, 120: 110, 135: -10, 150: -10, 180: -12000},
    
    (MERCURY, VENUS): {0: 33, 30: 2, 45: -2, 60: 6},
    
    (MOON, MERCURY): {0: 1643, 30: 6, 45: -6, 60: 41, 90: -41, 120: 41, 135: -6, 150: -6, 180: -1643},
    (MERCURY, MARS): {0: 9, 30: 2, 45: -2, 60: 3, 90: -3, 120: 3, 135: -2, 150: -2, 180: -9},
    (MERCURY, JUPITER): {0: 127, 30: 3, 45: -3, 60: 12, 90: -12, 120: 12, 135: -3, 150: -3, 180: -127},
    (MERCURY, SATURN): {0: 40, 30: 3, 45: -3, 60: 6, 90: -6, 120: 6, 135: -3, 150: -3, 180: -40},
    (MERCURY, URANUS): {0: 7, 30: 2, 45: -2, 60: 3, 90: -3, 120: 3, 135: -2, 150: -2, 180: -7},
    (MERCURY, NEPTUNE): {0: 5, 30: 1, 45: -1, 60: 2, 90: -2, 120: 2, 135: -1, 150: -1, 180: -5},
    (MOON, VENUS): {0: 6000, 30: 9, 45: -9, 60: 77, 90: -77, 120: 77, 135: -9, 150: -9, 180: -6000},
    (VENUS, MARS): {0: 33, 30: 2, 45: -2, 60: 8, 90: -8, 120: 8, 135: -2, 150: -2, 180: -33},
    (VENUS, JUPITER): {0: 465, 30: 5, 45: -5, 60: 22, 90: -22, 120: 22, 135: -5, 150: -5, 180: -465},
    (VENUS, SATURN): {0: 147, 30: 4, 45: -4, 60: 12, 90: -12, 120: 12, 135: -4, 150: -4, 180: -147},
    (VENUS, URANUS): {0: 27, 30: 3, 45: -3, 60: 5, 90: -5, 120: 5, 135: -3, 150: -3, 180: -27},
    (VENUS, NEPTUNE): {0: 19, 30: 2, 45: -2, 60: 4, 90: -4, 120: 4, 135: -2, 150: -2, 180: -19},
    (MOON, MARS): {0: 1643, 30: 6, 45: -6, 60: 41, 90: -41, 120: 41, 135: -6, 150: -6, 180: -1643},
    (MOON, JUPITER): {0: 23230, 30: 12, 45: -12, 60: 152, 90: -152, 120: 152, 135: -12, 150: -12, 180: -23230},
    (MOON, SATURN): {0: 7348, 30: 9, 45: -9, 60: 86, 90: -86, 120: 86, 135: -9, 150: -9, 180: -7348},
    (MOON, URANUS): {0: 1342, 30: 6, 45: -6, 60: 37, 90: -37, 120: 37, 135: -6, 150: -6, 180: -1342},
    (MOON, NEPTUNE): {0: 949, 30: 5, 45: -5, 60: 31, 90: -31, 120: 31, 135: -5, 150: -5, 180: -949},
    (MARS, JUPITER): {0: 127, 30: 3, 45: -3, 60: 11, 90: -11, 120: 11, 135: -3, 150: -3, 180: -127},
    (MARS, SATURN): {0: 40, 30: 3, 45: -3, 60: 6, 90: -6, 120: 6, 135: -3, 150: -3, 180: -40},
    (MARS, URANUS): {0: 7, 30: 2, 45: -2, 60: 3, 90: -3, 120: 3, 135: -2, 150: -2, 180: -7},
    (MARS, NEPTUNE): {0: 3, 30: 1, 45: -1, 60: 2, 90: -2, 120: 2, 135: -1, 150: -1, 180: -3},
    (JUPITER, SATURN): {0: 569, 30: 5, 45: -5, 60: 24, 90: -24, 120: 24, 135: -5, 150: -5, 180: -569},
    (JUPITER, URANUS): {0: 104, 30: 4, 45: -4, 60: 10, 90: -10, 120: 10, 135: -4, 150: -4, 180: -104},
    (JUPITER, NEPTUNE): {0: 74, 30: 3, 45: -3, 60: 9, 90: -9, 120: 9, 135: -3, 150: -3, 180: -74},
    (SATURN, URANUS): {0: 33, 30: 2, 45: -2, 60: 6, 90: -6, 120: 6, 135: -2, 150: -2, 180: -33},
    (SATURN, NEPTUNE): {0: 23, 30: 2, 45: -2, 60: 5, 90: -5, 120: 5, 135: -2, 150: -2, 180: -23},
    (URANUS, NEPTUNE): {0: 4, 30: 1, 45: -1, 60: 2, 90: -2, 120: 2, 135: -1, 150: -1, 180: -4}
}

# Оптимизированное кэширование: медленные планеты кэшируем по дням, быстрые - по минутам
@lru_cache(maxsize=16384)
def _pos_slow(planet: int, jd_day: int) -> float:
    pos, _ = swe.calc_ut(float(jd_day), planet)
    return pos[0]

@lru_cache(maxsize=262144)
def _pos_fast(planet: int, jd_minute: int) -> float:
    pos, _ = swe.calc_ut(jd_minute / 1440.0, planet)
    return pos[0]

def get_energy_for_jd(jd: float) -> int:
    jd_minute = round(jd * 1440)
    jd_day = int(jd)
    
    positions = {}
    for p in PLANETS:
        if p in FAST_PLANETS:
            positions[p] = _pos_fast(p, jd_minute)
        else:
            positions[p] = _pos_slow(p, jd_day)
        
    total_energy = 0
    for i in range(len(PLANETS)):
        for j in range(i + 1, len(PLANETS)):
            p1, p2 = PLANETS[i], PLANETS[j]
            pair = tuple(sorted([p1, p2]))
            
            if pair not in TABLE_1:
                continue
                
            diff = abs(positions[p1] - positions[p2])
            if diff > 180: diff = 360 - diff
                
            for aspect, orb in ASPECTS.items():
                if aspect in TABLE_1[pair]:
                    deviation = abs(diff - aspect)
                    if deviation <= orb:
                        # ИНТЕРПОЛЯЦИЯ (согласно стр. 186 методички ИППН)
                        power = 1.0 - (deviation / orb)
                        total_energy += TABLE_1[pair][aspect] * power
                        break # Планеты не могут быть в двух аспектах одновременно
    return round(total_energy)

def format_jd_to_utc(jd: float) -> str:
    y, m, d, h = swe.revjul(jd)
    minute = int((h - int(h)) * 60)
    return f"{y}-{m:02d}-{d:02d} {int(h):02d}:{minute:02d} UTC"

@app.get("/api/energy")
def get_energy(utc_timestamp: str):
    try:
        dt = datetime.datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат времени")
        
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
    score = get_energy_for_jd(jd)
    return {"utc_time": dt.strftime("%Y-%m-%d %H:%M UTC"), "score": score}

@app.get("/api/energy_batch")
def get_energy_batch(base_date: str, days_range: int = Query(15, ge=1, le=30)):
    try:
        y, m, d = map(int, base_date.split("-"))
        datetime.date(y, m, d)  # Валидация существования даты
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Неверный формат даты. Ожидается YYYY-MM-DD")
        
    base_jd = swe.julday(y, m, d, 12.0)
    
    results = []
    for i in range(-days_range, days_range + 1):
        jd = base_jd + i
        score = get_energy_for_jd(jd)
        ry, rm, rd, _ = swe.revjul(jd)
        results.append({"date": f"{rd:02d}.{rm:02d}", "score": score})
        
    return results

@app.get("/api/history")
def search_history(
    start_year: int = Query(..., ge=1800, le=2300),
    end_year: int = Query(..., ge=1800, le=2300),
    threshold: int = Query(...),
    condition: Literal["greater", "less"] = Query(...)
):
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="Год начала не может быть больше года конца")
    if end_year - start_year > 50:
        raise HTTPException(status_code=400, detail="Максимальный диапазон поиска: 50 лет (защита от перегрузки)")

    results = []
    jd_start = swe.julday(start_year, 1, 1, 0.0)
    jd_end = swe.julday(end_year, 12, 31, 0.0)
    
    step_coarse = 15.0 / 1440.0 # Шаг 15 минут для быстрого сканирования
    step_fine = 1.0 / 1440.0    # Шаг 1 минута для точного поиска границ
    
    current_jd = jd_start
    in_window = False
    window_start_jd = None
    window_peak_jd = None
    window_max_score = 0
    
    while current_jd <= jd_end:
        score = get_energy_for_jd(current_jd)
        triggered = (condition == "greater" and score >= threshold) or \
                    (condition == "less" and score <= threshold)
        
        if triggered and not in_window:
            fine_jd = current_jd
            while fine_jd > current_jd - step_coarse:
                fine_jd -= step_fine
                fine_score = get_energy_for_jd(fine_jd)
                fine_triggered = (condition == "greater" and fine_score >= threshold) or \
                                 (condition == "less" and fine_score <= threshold)
                if not fine_triggered:
                    break
            window_start_jd = fine_jd + step_fine
            window_max_score = score
            window_peak_jd = current_jd
            in_window = True
            
        elif in_window:
            if (condition == "greater" and score > window_max_score) or \
               (condition == "less" and score < window_max_score):
                window_max_score = score
                window_peak_jd = current_jd
                
            if not triggered:
                fine_jd = current_jd
                while fine_jd > current_jd - step_coarse:
                    fine_jd -= step_fine
                    fine_score = get_energy_for_jd(fine_jd)
                    fine_triggered = (condition == "greater" and fine_score >= threshold) or \
                                     (condition == "less" and fine_score <= threshold)
                    if fine_triggered:
                        break
                window_end_jd = fine_jd
                
                results.append({
                    "start_utc": format_jd_to_utc(window_start_jd),
                    "peak_utc": format_jd_to_utc(window_peak_jd),
                    "end_utc": format_jd_to_utc(window_end_jd),
                    "score": window_max_score
                })
                in_window = False
                
                if len(results) >= 50:
                    break
                    
        current_jd += step_coarse
        
    results.sort(key=lambda x: abs(x["score"]), reverse=True)
    return {"results": results[:50]}

# Кэшируем HTML в памяти при старте
with open("index.html", "r", encoding="utf-8") as f:
    _HTML_CONTENT = f.read()

@app.get("/")
def read_root():
    return HTMLResponse(content=_HTML_CONTENT)
