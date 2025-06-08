# utils/config.py
from utils.enums import ChargeMode

# Pricing per kWh
PRICE_PER_KWH = {
    ChargeMode.FAST: 1.2,
    ChargeMode.TRICKLE: 0.8
}

# Service fee per charging session
SERVICE_FEE = 2.0