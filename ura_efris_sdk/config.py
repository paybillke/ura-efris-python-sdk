import os
from typing import Dict, Any, Optional


def load_config_from_env(
    prefix: str = "EFRIS",
    sandbox_default: bool = True
) -> Dict[str, Any]:
    """
    Load EFRIS config from environment variables.
    
    Expected env vars:
    - {prefix}_ENV: "sbx" or "prod" (default: "sbx")
    - {prefix}_TIN: Taxpayer TIN (required)
    - {prefix}_DEVICE_NO: URA-assigned device number (required)
    - {prefix}_BRN: Business Registration Number (optional)
    - {prefix}_PFX_PATH: Path to .pfx certificate file (required)
    - {prefix}_PFX_PASSWORD: Password for .pfx file (required) - RAW, no decryption
    - {prefix}_HTTP_TIMEOUT: Request timeout in seconds (default: 30)
    """
    def get_env(key: str, default: Any = None, required: bool = False) -> Any:
        env_key = f"{prefix}_{key}"
        value = os.getenv(env_key, default)
        if required and not value:
            raise ValueError(f"Missing required environment variable: {env_key}")
        return value
    
    return {
        "env": get_env("ENV", "sbx" if sandbox_default else "prod"),
        "tin": get_env("TIN", required=True),
        "device_no": get_env("DEVICE_NO", required=True),
        "brn": get_env("BRN", ""),
        "pfx_path": get_env("PFX_PATH", required=True),
        "pfx_password": get_env("PFX_PASSWORD", required=True),  # RAW from env
        "user": get_env("USER", "admin"),
        "longitude": get_env("LONGITUDE", "32.5825"),
        "latitude": get_env("LATITUDE", "0.3476"),
        "http": {
            "timeout": int(get_env("HTTP_TIMEOUT", "30"))
        }
    }


def validate_config(config: Dict[str, Any]) -> None:
    """Validate config has required fields"""
    required = ["env", "tin", "device_no", "pfx_path", "pfx_password"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"Missing required config fields: {missing}")
    
    if config["env"] not in ["sbx", "prod"]:
        raise ValueError(f"Invalid env: {config['env']}. Must be 'sbx' or 'prod'")
    
    if not os.path.exists(config["pfx_path"]):
        raise ValueError(f"PFX file not found: {config['pfx_path']}")