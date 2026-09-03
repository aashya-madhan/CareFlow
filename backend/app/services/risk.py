"""Risk score computation — mirrors the JS logic in data.js"""


def compute_risk_score(
    previous_no_shows: int,
    lead_days: int,
    sms_received: bool,
    scholarship: bool,
    alcoholism: bool,
    age: int,
) -> int:
    score = 0

    if previous_no_shows >= 3:
        score += 35
    elif previous_no_shows == 2:
        score += 22
    elif previous_no_shows == 1:
        score += 12

    if lead_days > 30:
        score += 20
    elif lead_days > 14:
        score += 12
    elif lead_days > 7:
        score += 6

    if not sms_received:
        score += 15

    if scholarship:
        score += 8

    if alcoholism:
        score += 10

    if 18 <= age <= 35:
        score += 8
    elif age < 18:
        score += 5

    return min(score, 99)


def get_risk_label(score: int) -> str:
    if score >= 55:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"
