"""
EFRIS Configuration Management
Handles loading and validating configuration from environment variables.
"""
import os
from typing import Dict, Any, Optional


def load_config_from_env(
    prefix: str = "EFRIS",
    sandbox_default: bool = True
) -> Dict[str, Any]:
    """
    Load EFRIS configuration from environment variables.
    
    Environment Variables:
        EFRIS_ENV: Environment (sbx/prod)
        EFRIS_TIN: Taxpayer Identification Number (required)
        EFRIS_DEVICE_NO: Device serial number (required)
        EFRIS_BRN: Business Registration Number
        EFRIS_PFX_PATH: Path to PFX certificate file (required)
        EFRIS_PFX_PASSWORD: PFX file password (required)
        EFRIS_USER: Username (default: admin)
        EFRIS_LONGITUDE: GPS longitude (default: 32.5825)
        EFRIS_LATITUDE: GPS latitude (default: 0.3476)
        EFRIS_HTTP_TIMEOUT: HTTP request timeout in seconds (default: 30)
    
    Args:
        prefix: Environment variable prefix
        sandbox_default: Use sandbox environment by default
    
    Returns:
        dict: Configuration dictionary
    
    Raises:
        ValueError: If required environment variables are missing
    """
    def get_env(
        key: str,
        default: Any = None,
        required: bool = False
    ) -> Any:
        """Helper to get environment variable with validation."""
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
        "pfx_password": get_env("PFX_PASSWORD", required=True),
        "user": get_env("USER", "admin"),
        "longitude": get_env("LONGITUDE", "32.5825"),
        "latitude": get_env("LATITUDE", "0.3476"),
        "http": {
            "timeout": int(get_env("HTTP_TIMEOUT", "30"))
        }
    }


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration dictionary.
    
    Checks:
        - Required fields are present
        - Environment is valid (sbx/prod)
        - PFX file exists at specified path
    
    Args:
        config: Configuration dictionary
    
    Raises:
        ValueError: If validation fails
    """
    required = ["env", "tin", "device_no", "pfx_path", "pfx_password"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"Missing required config fields: {missing}")
    
    if config["env"] not in ["sbx", "prod"]:
        raise ValueError(f"Invalid env: {config['env']}. Must be 'sbx' or 'prod'")
    
    if not os.path.exists(config["pfx_path"]):
        raise ValueError(f"PFX file not found: {config['pfx_path']}")