import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CityPulse — Greater Mumbai Flood Risk & Critical Infrastructure"
    API_V1_STR: str = "/api/v1"
    SIH_PROJECT_CODE: str = "SIH26085"
    STUDY_AREA: str = "Brihanmumbai Municipal Corporation (BMC / MCGM) & Mumbai Metropolitan Area"
    MODEL_VERSION: str = "XGBoost-v1.1-Mumbai-HotspotProxy"
    DATA_MODE: str = "mumbai_verified_pipeline"
    USE_DEVELOPMENT_FALLBACK: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:4200", "http://127.0.0.1:4200",
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:8080", "http://127.0.0.1:8080",
    ]
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Geographic Bounding Box & Center (Mumbai UTM 43N / WGS84)
    DEFAULT_LAT: float = 19.0760
    DEFAULT_LON: float = 72.8777
    BOUNDS_MIN_LAT: float = 18.89
    BOUNDS_MAX_LAT: float = 19.30
    BOUNDS_MIN_LON: float = 72.75
    BOUNDS_MAX_LON: float = 73.02
    CRS_PROJECTED: str = "EPSG:32643"
    CRS_GEOGRAPHIC: str = "EPSG:4326"

    # Security & JWT — override SECRET_KEY in production via environment
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-only-change-me-citypulse-mumbai")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/floodwatch.db")

    # Environment & Demo Seed
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ENABLE_DEMO_SEED: bool = os.getenv("ENABLE_DEMO_SEED", "true").lower() == "true"

    # Alert Geofence & Location Retention
    ALERT_ZONE_BUFFER_METERS: float = 500.0
    ALERT_COOLDOWN_MINUTES: int = 30
    LOCATION_MAX_AGE_HOURS: int = 4
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5

    # CityPulse Decision Support Extensions
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    GRID_GEOJSON_PATH: str = os.getenv("GRID_GEOJSON_PATH", "./data/processed/grids/mumbai_grid_500m.geojson")
    STATIC_FEATURES_PATH: str = os.getenv("STATIC_FEATURES_PATH", "./data/processed/features/mumbai_static_spatial_features.parquet")
    CRITICAL_INFRA_PATH: str = os.getenv("CRITICAL_INFRA_PATH", "./data/processed/vectors/mumbai_critical_infrastructure.parquet")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models/trained/mumbai_xgboost_baseline.json")

    DEFAULT_INSPECTION_BUDGET: int = 5
    DISRUPTION_THRESHOLD_HIGH: float = 0.50
    DISRUPTION_THRESHOLD_CRITICAL: float = 0.75

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()