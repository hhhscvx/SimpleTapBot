from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BalanceResult:
    active_farming_balance: float
    active_farming_seconds: int
    max_farming_seconds: int
    available_taps: int
    max_available_taps: int
    tap_size: int
    spin_count: int
