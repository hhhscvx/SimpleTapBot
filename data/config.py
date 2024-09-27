from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    API_ID: int
    API_HASH: str

    RANDOM_TAPS_COUNT: list[int] = [3, 13]
    SLEEP_BETWEEN_TAP: list[float] = [0.8, 3.0]
    MIN_AVAILABLE_TAPS: int = 10
    SLEEP_BY_MIN_ENERGY: list[int] = [600, 1800]

    DO_TASKS: bool = False  # almost all tasks must be done manually

    USE_PROXY_FROM_FILE: bool = False  # True - if use proxy from file, False - if use proxy from accounts.json
    PROXY_PATH: str = "data/proxy.txt"
    PROXY_TYPE_TG: str = "socks5"  # proxy type for tg client. "socks4", "socks5" and "http" are supported
    # proxy type for requests. "http" for https and http proxys, "socks5" for socks5 proxy.
    PROXY_TYPE_REQUESTS: str = "socks5"

    WORKDIR: str = 'sessions/'

    # timeout in seconds for checking accounts on valid
    TIMEOUT: int = 30

    DELAY_CONN_ACCOUNT: list[int] = [5, 15]


config = Settings()
