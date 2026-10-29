"""
Part 2 - Analytical metrics for Really Big Bank.

Reads the validated CSVs produced by pipeline.py and writes a curated
layer in curated/ that the Part 3 dashboard can read directly.

Run pipeline.py first, then:  python3 metrics.py
"""
from pathlib import Path
from datetime import date
import csv
import math
import statistics

BASE = Path(__file__).resolve().parent
PROCESSED = BASE / "processed"
CURATED = BASE / "curated"
LOGS = BASE / "logs"
CURATED.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)

TRADING_DAYS = 252      # used to annualise volatility
MA_SHORT = 20           # about one trading month
MA_LONG = 50            # about one trading quarter
VOL_WINDOW = 20
EVENT_WINDOW = 5        # trading days either side of a rate decision

notes = []


def note(metric, detail):
    notes.append([metric, detail])


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def save_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def rnd(value, places=2):
    return "" if value is None else round(value, places)


# 1. Load processed data -------------------------------------------------
rba = [(date.fromisoformat(r["Date"]), float(r["Cash Rate Target (%)"]))
       for r in read_csv(PROCESSED / "rba_clean.csv")]
asx = read_csv(PROCESSED / "asx200_clean.csv")

dates = [date.fromisoformat(r["Date"]) for r in asx]
close = [float(r["Close"]) for r in asx]
volume = [float(r["Volume"]) if r["Volume"] else None for r in asx]

if dates != sorted(dates):
    raise ValueError("ASX dates are not in order - rerun pipeline.py")


# 2. Cash rate metrics -----------------------------------------------------
# Rate decisions are the days the target differs from the previous day.
rate_changes = []
for (d0, r0), (d1, r1) in zip(rba, rba[1:]):
    if r1 != r0:
        rate_changes.append((d1, r0, r1, round((r1 - r0) * 100)))


def cash_rate_on(day):
    """Latest published cash rate on or before a given day (as-of join)."""
    rate = None
    for d, r in rba:
        if d > day:
            break
        rate = r
    return rate


# 3. ASX 200 metrics -------------------------------------------------------
daily_return = [None] + [
    (close[i] / close[i - 1] - 1) * 100 for i in range(1, len(close))
]


def moving_average(values, window, i):
    if i + 1 < window:
        return None
    return sum(values[i + 1 - window:i + 1]) / window


def rolling_vol(i):
    window = daily_return[i + 1 - VOL_WINDOW:i + 1]
    if i < VOL_WINDOW or None in window:
        return None
    return statistics.stdev(window) * math.sqrt(TRADING_DAYS)


def avg_volume(i):
    window = [v for v in volume[max(0, i + 1 - MA_SHORT):i + 1]
              if v is not None]
    return sum(window) / len(window) if len(window) == MA_SHORT else None


peak = close[0]
change_dates = {c[0] for c in rate_changes}
rows = []
for i, d in enumerate(dates):
    peak = max(peak, close[i])
    ma_s = moving_average(close, MA_SHORT, i)
    ma_l = moving_average(close, MA_LONG, i)
    trend = ""
    if ma_s is not None and ma_l is not None:
        trend = "Up" if ma_s > ma_l else "Down"
    rows.append([
        d.isoformat(), close[i], rnd(daily_return[i], 3),
        rnd(ma_s), rnd(ma_l), trend,
        rnd(rolling_vol(i)), rnd((close[i] / peak - 1) * 100),
        "" if volume[i] is None else int(volume[i]), rnd(avg_volume(i), 0),
        cash_rate_on(d), "Yes" if d in change_dates else "No",
    ])

missing_vol = [dates[i].isoformat() for i, v in enumerate(volume) if v is None]
if missing_vol:
    note("20-day average volume",
         f"Left blank where the window includes missing volume: "
         f"{', '.join(missing_vol)}")
note("Moving averages",
     f"First {MA_SHORT - 1} and {MA_LONG - 1} rows blank (not enough history)")


# 4. Event analysis: ASX reaction around each rate decision ---------------
events = []
for d, old, new, bps in rate_changes:
    if not (dates[0] <= d <= dates[-1]):
        continue
    i = next(k for k, x in enumerate(dates) if x >= d)
    before = i - EVENT_WINDOW
    after = i + EVENT_WINDOW
    if before < 0 or after >= len(dates):
        note("Rate event window", f"{d} skipped, window falls outside data")
        continue
    events.append([
        d.isoformat(), old, new, bps,
        "Increase" if bps > 0 else "Decrease",
        rnd((close[i - 1] / close[before] - 1) * 100),
        rnd(daily_return[i], 3),
        rnd((close[after] / close[i - 1] - 1) * 100),
    ])


# 5. KPI summary for the dashboard header ---------------------------------
last = len(close) - 1
latest_rate = rba[-1][1]
year_ago = date(rba[-1][0].year - 1, rba[-1][0].month, rba[-1][0].day)
rate_12m_ago = cash_rate_on(year_ago)
last_change = rate_changes[-1]
valid_returns = [r for r in daily_return if r is not None]

kpis = [
    ["Reporting date", dates[last].isoformat(), ""],
    ["ASX 200 close", close[last], "points"],
    ["ASX 200 12-month return", rnd((close[last] / close[0] - 1) * 100), "%"],
    ["Maximum drawdown", rnd(min(float(r[7]) for r in rows)), "%"],
    ["Current 20-day volatility", rows[last][6], "% annualised"],
    ["Full-period volatility",
     rnd(statistics.stdev(valid_returns) * math.sqrt(TRADING_DAYS)),
     "% annualised"],
    ["Trend signal (MA20 vs MA50)", rows[last][5], ""],
    ["Cash rate target", latest_rate, "%"],
    ["Cash rate change, last 12 months",
     round((latest_rate - rate_12m_ago) * 100), "bps"],
    ["Last rate decision", last_change[0].isoformat(), ""],
    ["Days since last rate change", (rba[-1][0] - last_change[0]).days, "days"],
    ["Rate decisions in ASX window", len(events), "count"],
]


# 6. Save curated layer ----------------------------------------------------
save_csv(CURATED / "asx200_daily_metrics.csv",
         ["Date", "Close", "Daily Return (%)", "MA20", "MA50", "Trend",
          "Volatility 20d (% ann.)", "Drawdown (%)", "Volume",
          "Avg Volume 20d", "Cash Rate Target (%)", "Rate Decision Day"],
         rows)
save_csv(CURATED / "rate_changes.csv",
         ["Date", "Previous Rate (%)", "New Rate (%)", "Change (bps)"],
         [[d.isoformat(), o, n, b] for d, o, n, b in rate_changes])
save_csv(CURATED / "rate_event_impact.csv",
         ["Decision Date", "Previous Rate (%)", "New Rate (%)",
          "Change (bps)", "Direction", f"ASX Return {EVENT_WINDOW}d Before (%)",
          "ASX Return On Day (%)", f"ASX Return {EVENT_WINDOW}d After (%)"],
         events)
save_csv(CURATED / "kpi_summary.csv", ["Metric", "Value", "Unit"], kpis)
save_csv(LOGS / "metrics_notes.csv", ["Metric", "Note"], notes)

print("Metrics completed!")
print(f"ASX 200 daily metric rows: {len(rows)}")
print(f"Cash rate decisions found: {len(rate_changes)}")
print(f"Rate decisions analysed against ASX 200: {len(events)}")
print("Outputs saved in curated/ and logs/metrics_notes.csv")
