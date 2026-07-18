"""
Calculates door-to-door time for Route A (Q→R/W or R/W→Q) and Route B (6 direct).
"""

from datetime import datetime, timedelta
import config
from mta_feed import get_arrivals


def _wait_minutes(arrivals, arrive_at_platform_dt):
    """Minutes until the first train departing after arrive_at_platform_dt."""
    for t in arrivals:
        if t >= arrive_at_platform_dt:
            return (t - arrive_at_platform_dt).total_seconds() / 60, t
    return None, None  # no train found in feed window


def calculate_routes(direction):
    """
    direction: "to_work" or "to_home"
    Returns dict with keys: route_a, route_b, winner, savings_minutes
    Each route: total_minutes, departs_dt, arrives_dt, catch_train_dt, valid (bool)
    """
    now = datetime.now()
    arrivals = get_arrivals(direction)

    if direction == "to_work":
        result_a = _calc_route_a_to_work(now, arrivals)
        result_b = _calc_route_b_to_work(now, arrivals)
    else:
        result_a = _calc_route_a_to_home(now, arrivals)
        result_b = _calc_route_b_to_home(now, arrivals)

    winner = None
    savings = None
    if result_a["valid"] and result_b["valid"]:
        if result_a["total_minutes"] <= result_b["total_minutes"]:
            winner = "A"
            savings = round(result_b["total_minutes"] - result_a["total_minutes"])
        else:
            winner = "B"
            savings = round(result_a["total_minutes"] - result_b["total_minutes"])
    elif result_a["valid"]:
        winner = "A"
    elif result_b["valid"]:
        winner = "B"

    return {
        "route_a": result_a,
        "route_b": result_b,
        "winner": winner,
        "savings_minutes": savings,
        "calculated_at": now,
    }


def _calc_route_a_to_work(now, arrivals):
    walk1 = config.WALK_HOME_TO_72ND_Q
    arrive_72nd = now + timedelta(minutes=walk1)

    stop = config.STOP_72ND_Q_SB
    if not stop or stop not in arrivals:
        return _invalid()
    wait_q, q_departs = _wait_minutes(arrivals[stop], arrive_72nd)
    if wait_q is None:
        return _invalid()

    arrive_34th = q_departs + timedelta(minutes=config.RIDE_Q_72ND_TO_34TH)
    arrive_34th_rw = arrive_34th + timedelta(minutes=config.TRANSFER_34TH_BUFFER)

    stop_rw = config.STOP_34TH_RW_SB
    if not stop_rw or stop_rw not in arrivals:
        return _invalid()
    wait_rw, rw_departs = _wait_minutes(arrivals[stop_rw], arrive_34th_rw)
    if wait_rw is None:
        return _invalid()

    arrive_23rd = rw_departs + timedelta(minutes=config.RIDE_RW_34TH_TO_23RD)
    arrive_office = arrive_23rd + timedelta(minutes=config.WALK_23RD_RW_TO_OFFICE)
    total = (arrive_office - now).total_seconds() / 60

    return {
        "valid": True,
        "total_minutes": round(total),
        "departs_dt": q_departs,
        "arrives_dt": arrive_office,
        "label": "Q → R/W",
    }


def _calc_route_b_to_work(now, arrivals):
    walk1 = config.WALK_HOME_TO_77TH_6
    arrive_77th = now + timedelta(minutes=walk1)

    stop = config.STOP_77TH_6_SB
    if not stop or stop not in arrivals:
        return _invalid()
    wait_6, six_departs = _wait_minutes(arrivals[stop], arrive_77th)
    if wait_6 is None:
        return _invalid()

    arrive_28th = six_departs + timedelta(minutes=config.RIDE_6_77TH_TO_28TH)
    arrive_office = arrive_28th + timedelta(minutes=config.WALK_28TH_6_TO_OFFICE)
    total = (arrive_office - now).total_seconds() / 60

    return {
        "valid": True,
        "total_minutes": round(total),
        "departs_dt": six_departs,
        "arrives_dt": arrive_office,
        "label": "6",
    }


def _calc_route_a_to_home(now, arrivals):
    walk1 = config.WALK_OFFICE_TO_23RD_RW
    arrive_23rd = now + timedelta(minutes=walk1)

    stop = config.STOP_23RD_RW_NB
    if not stop or stop not in arrivals:
        return _invalid()
    wait_rw, rw_departs = _wait_minutes(arrivals[stop], arrive_23rd)
    if wait_rw is None:
        return _invalid()

    arrive_34th = rw_departs + timedelta(minutes=config.RIDE_RW_23RD_TO_34TH)
    arrive_34th_q = arrive_34th + timedelta(minutes=config.TRANSFER_34TH_BUFFER)

    stop_q = config.STOP_34TH_Q_NB
    if not stop_q or stop_q not in arrivals:
        return _invalid()
    wait_q, q_departs = _wait_minutes(arrivals[stop_q], arrive_34th_q)
    if wait_q is None:
        return _invalid()

    arrive_72nd = q_departs + timedelta(minutes=config.RIDE_Q_34TH_TO_72ND)
    arrive_home = arrive_72nd + timedelta(minutes=config.WALK_72ND_Q_TO_HOME)
    total = (arrive_home - now).total_seconds() / 60

    return {
        "valid": True,
        "total_minutes": round(total),
        "departs_dt": rw_departs,
        "arrives_dt": arrive_home,
        "label": "R/W → Q",
    }


def _calc_route_b_to_home(now, arrivals):
    walk1 = config.WALK_OFFICE_TO_28TH_6
    arrive_28th = now + timedelta(minutes=walk1)

    stop = config.STOP_28TH_6_NB
    if not stop or stop not in arrivals:
        return _invalid()
    wait_6, six_departs = _wait_minutes(arrivals[stop], arrive_28th)
    if wait_6 is None:
        return _invalid()

    arrive_77th = six_departs + timedelta(minutes=config.RIDE_6_28TH_TO_77TH)
    arrive_home = arrive_77th + timedelta(minutes=config.WALK_77TH_6_TO_HOME)
    total = (arrive_home - now).total_seconds() / 60

    return {
        "valid": True,
        "total_minutes": round(total),
        "departs_dt": six_departs,
        "arrives_dt": arrive_home,
        "label": "6",
    }


def _invalid():
    return {"valid": False, "total_minutes": None, "departs_dt": None, "arrives_dt": None, "label": None}
