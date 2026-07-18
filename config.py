# Walking times (minutes)
WALK_HOME_TO_72ND_Q = 12
WALK_HOME_TO_77TH_6 = 16
WALK_23RD_RW_TO_OFFICE = 10
WALK_28TH_6_TO_OFFICE = 5
WALK_OFFICE_TO_23RD_RW = 10
WALK_OFFICE_TO_28TH_6 = 7
WALK_72ND_Q_TO_HOME = 12
WALK_77TH_6_TO_HOME = 16

TRANSFER_34TH_BUFFER = 3
REFRESH_INTERVAL_SECONDS = 60

# Ride times (minutes, approximate)
RIDE_Q_72ND_TO_34TH = 8
RIDE_RW_34TH_TO_23RD = 4
RIDE_RW_23RD_TO_34TH = 4
RIDE_Q_34TH_TO_72ND = 8
RIDE_6_77TH_TO_28TH = 6
RIDE_6_28TH_TO_77TH = 6

# Known stop IDs
STOP_28TH_6_NB = "634N"
STOP_77TH_6_NB = "631N"
STOP_77TH_6_SB = "631S"
STOP_28TH_6_SB = "634S"

# Resolved at first boot by lookup_stops.py if None
STOP_72ND_Q_SB = None   # 72nd St Q southbound (to work)
STOP_72ND_Q_NB = None   # 72nd St Q northbound (to home)
STOP_34TH_Q_NB = None   # 34th St Q northbound (transfer, to home)
STOP_34TH_Q_SB = None   # 34th St Q southbound (transfer, to work) — same station, opposite platform
STOP_34TH_RW_SB = None  # 34th St R/W southbound (to work)
STOP_34TH_RW_NB = None  # 34th St R/W northbound (to home)
STOP_23RD_RW_SB = None  # 23rd St R/W southbound (to work)
STOP_23RD_RW_NB = None  # 23rd St R/W northbound (to home)
