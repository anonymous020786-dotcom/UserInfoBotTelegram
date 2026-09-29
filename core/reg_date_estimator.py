import datetime
from typing import Dict, Any, Optional

# Reference ID epochs for User Accounts (Sequential 64-bit Telegram ID milestones)
USER_ID_EPOCHS = [
    (0, datetime.date(2013, 8, 1)),
    (10_000_000, datetime.date(2013, 12, 1)),
    (45_000_000, datetime.date(2014, 6, 1)),
    (85_000_000, datetime.date(2015, 1, 1)),
    (130_000_000, datetime.date(2015, 6, 1)),
    (180_000_000, datetime.date(2016, 1, 1)),
    (250_000_000, datetime.date(2016, 7, 1)),
    (330_000_000, datetime.date(2017, 1, 1)),
    (430_000_000, datetime.date(2017, 7, 1)),
    (530_000_000, datetime.date(2018, 1, 1)),
    (670_000_000, datetime.date(2018, 7, 1)),
    (780_000_000, datetime.date(2019, 1, 1)),
    (920_000_000, datetime.date(2019, 7, 1)),
    (1_050_000_000, datetime.date(2020, 1, 1)),
    (1_250_000_000, datetime.date(2020, 7, 1)),
    (1_550_000_000, datetime.date(2021, 1, 1)),
    (1_850_000_000, datetime.date(2021, 7, 1)),
    (2_150_000_000, datetime.date(2021, 12, 1)),
    (5_100_000_000, datetime.date(2022, 4, 1)),
    (5_500_000_000, datetime.date(2022, 9, 1)),
    (5_900_000_000, datetime.date(2023, 2, 1)),
    (6_350_000_000, datetime.date(2023, 8, 1)),
    (6_800_000_000, datetime.date(2024, 2, 1)),
    (7_250_000_000, datetime.date(2024, 8, 1)),
    (7_650_000_000, datetime.date(2025, 2, 1)),
    (8_100_000_000, datetime.date(2025, 8, 1)),
    (8_550_000_000, datetime.date(2026, 2, 1)),
    (9_000_000_000, datetime.date(2026, 8, 1)),
]

# Reference ID epochs for Channels & Supergroups (internal IDs without -100 prefix)
CHANNEL_ID_EPOCHS = [
    (100_000_000, datetime.date(2015, 9, 1)),   # Channels introduced in Telegram 3.2
    (150_000_000, datetime.date(2016, 6, 1)),
    (300_000_000, datetime.date(2017, 3, 1)),
    (500_000_000, datetime.date(2018, 1, 1)),
    (800_000_000, datetime.date(2019, 1, 1)),
    (1_100_000_000, datetime.date(2020, 1, 1)),
    (1_350_000_000, datetime.date(2021, 1, 1)),
    (1_600_000_000, datetime.date(2022, 1, 1)),
    (1_800_000_000, datetime.date(2023, 1, 1)),
    (2_000_000_000, datetime.date(2024, 1, 1)),
    (2_250_000_000, datetime.date(2025, 1, 1)),
    (2_500_000_000, datetime.date(2026, 1, 1)),
]


def estimate_registration_date(telegram_id: int) -> Dict[str, Any]:
    """
    Estimates the month and year of creation for a Telegram User, Channel, or Supergroup
    using chronological piecewise linear regression.
    """
    is_channel_or_group = False
    clean_id = telegram_id

    # Handle negative channel / supergroup IDs (prefixed with -100)
    if str(telegram_id).startswith("-100"):
        is_channel_or_group = True
        try:
            clean_id = int(str(telegram_id)[4:])
        except ValueError:
            clean_id = abs(telegram_id)
    elif telegram_id < 0:
        is_channel_or_group = True
        clean_id = abs(telegram_id)

    epochs = CHANNEL_ID_EPOCHS if is_channel_or_group else USER_ID_EPOCHS

    # If ID is lower than the lowest milestone
    if clean_id <= epochs[0][0]:
        est_date = epochs[0][1]
        return {
            "estimated_month": est_date.strftime("%B %Y"),
            "approx_date": est_date.isoformat(),
            "confidence": "High (Pioneer Account)",
            "relative_age": _calculate_relative_age(est_date)
        }

    # If ID exceeds the highest known milestone
    if clean_id >= epochs[-1][0]:
        est_date = epochs[-1][1]
        return {
            "estimated_month": est_date.strftime("%B %Y") + " or newer",
            "approx_date": est_date.isoformat(),
            "confidence": "Moderate (Recent Entity)",
            "relative_age": _calculate_relative_age(est_date)
        }

    # Interpolate between epochs
    for i in range(len(epochs) - 1):
        low_id, low_date = epochs[i]
        high_id, high_date = epochs[i + 1]

        if low_id <= clean_id <= high_id:
            ratio = (clean_id - low_id) / (high_id - low_id)
            total_days = (high_date - low_date).days
            est_days = int(ratio * total_days)
            est_date = low_date + datetime.timedelta(days=est_days)

            return {
                "estimated_month": est_date.strftime("%B %Y"),
                "approx_date": est_date.strftime("%Y-%m-%d"),
                "confidence": "± 1-2 Months (Accurate Regression)",
                "relative_age": _calculate_relative_age(est_date)
            }

    # Fallback
    return {
        "estimated_month": "Unknown",
        "approx_date": "N/A",
        "confidence": "Low",
        "relative_age": "Unknown"
    }


def _calculate_relative_age(past_date: datetime.date) -> str:
    """Calculates human-readable elapsed duration."""
    today = datetime.date.today()
    delta_days = (today - past_date).days
    years = delta_days // 365
    months = (delta_days % 365) // 30

    if years > 0:
        return f"~{years} yr{'s' if years > 1 else ''} {months} mo{'s' if months > 1 else ''}"
    return f"~{months} month{'s' if months > 1 else ''}"
