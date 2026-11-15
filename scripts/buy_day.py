"""This month's buy day: the 15th, or the next day both New York and London are open if the 15th isn't.
Used by the monthly reminder so it never says 'buy today' on a weekend or market holiday.
Prints two lines: the buy date (YYYY-MM-DD) and whether the reminder should go out now (send / wait)."""
import sys
from datetime import date, datetime, timedelta, timezone


def nth_weekday(y, m, weekday, n):            # weekday: Monday=0
    d = date(y, m, 1); d += timedelta((weekday - d.weekday()) % 7)
    return d + timedelta(7 * (n - 1))


def easter(y):                                # Anonymous Gregorian algorithm
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mo = (h + l - 7 * m + 114) // 31; da = (h + l - 7 * m + 114) % 31 + 1
    return date(y, mo, da)


def closed(d):
    """Weekends plus the US and UK market holidays that can fall on or just after the 15th."""
    if d.weekday() >= 5: return True
    y = d.year
    hol = {nth_weekday(y, 1, 0, 3), nth_weekday(y, 2, 0, 3),        # MLK Day, Presidents' Day (3rd Monday)
           easter(y) - timedelta(2), easter(y) + timedelta(1)}      # Good Friday (both), Easter Monday (London)
    jun19 = date(y, 6, 19)                                          # Juneteenth, moved off weekends
    hol.add(jun19 - timedelta(1) if jun19.weekday() == 5 else jun19 + timedelta(1) if jun19.weekday() == 6 else jun19)
    return d in hol


def buy_date(y, m):
    d = date(y, m, 15)
    while closed(d): d += timedelta(1)
    return d


def prev_open(d):
    d -= timedelta(1)
    while d.weekday() >= 5: d -= timedelta(1)
    return d


if __name__ == "__main__":
    today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(timezone(timedelta(hours=8))).date()
    b = buy_date(today.year, today.month)
    # Remind the day before the buy day (Hong Kong time), or on the buy day itself if every earlier try was missed.
    send = date(b.year, b.month, b.day) - timedelta(1) <= today <= b
    print(b.isoformat()); print("send" if send else "wait")
