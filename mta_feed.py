"""
Polls MTA GTFS-RT feeds for the 6 line and NQR lines.
Caches responses for 30 seconds.
"""

import time
from datetime import datetime
from nyct_gtfs import NYCTFeed
import config

_cache = {}
_CACHE_TTL = 30  # seconds

FEED_6 = "6"
FEED_NQR = "nqr"

RELEVANT_STOPS = {
    "to_work": {
        "6":  [config.STOP_77TH_6_SB, config.STOP_28TH_6_SB],
        "nqr": [],  # filled at call time after stop lookup
    },
    "to_home": {
        "6":  [config.STOP_28TH_6_NB, config.STOP_77TH_6_NB],
        "nqr": [],
    },
}


def _get_feed(feed_id):
    now = time.time()
    if feed_id in _cache:
        feed, ts = _cache[feed_id]
        if now - ts < _CACHE_TTL:
            return feed
    feed = NYCTFeed(feed_id)
    _cache[feed_id] = (feed, now)
    return feed


def _arrivals_at_stop(feed, stop_id, n=3):
    """Return next n departure datetimes at stop_id."""
    now = datetime.now()
    times = []
    for trip in feed.trips:
        for update in trip.stop_time_updates:
            if update.stop_id == stop_id:
                t = update.departure or update.arrival
                if t and t > now:
                    times.append(t)
    times.sort()
    return times[:n]


def get_arrivals(direction):
    """
    Return dict of stop_id -> list of up to 3 departure datetimes.
    direction: "to_work" or "to_home"
    """
    nqr_stops = (
        [config.STOP_72ND_Q_SB, config.STOP_34TH_Q_SB, config.STOP_34TH_RW_SB, config.STOP_23RD_RW_SB]
        if direction == "to_work"
        else [config.STOP_23RD_RW_NB, config.STOP_34TH_RW_NB, config.STOP_34TH_Q_NB, config.STOP_72ND_Q_NB]
    )
    line6_stops = (
        [config.STOP_77TH_6_SB, config.STOP_28TH_6_SB]
        if direction == "to_work"
        else [config.STOP_28TH_6_NB, config.STOP_77TH_6_NB]
    )

    feed6 = _get_feed(FEED_6)
    feed_nqr = _get_feed(FEED_NQR)

    result = {}
    for stop_id in line6_stops:
        if stop_id:
            result[stop_id] = _arrivals_at_stop(feed6, stop_id)
    for stop_id in nqr_stops:
        if stop_id:
            result[stop_id] = _arrivals_at_stop(feed_nqr, stop_id)

    return result
