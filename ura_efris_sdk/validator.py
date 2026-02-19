from typing import Dict, Any, Optional
from pydantic import ValidationError
from .schemas import SCHEMAS
from .exceptions import ValidationException


class Validator:
    """
    Validates request payloads against Pydantic schemas.
    Converts validation errors to ValidationException with field-level messages.
    """
    
    def validate(self, data: Dict[str, Any], schema_key: str) -> Dict[str, Any]:
        """
        Validate data against schema.
        
        Args:
            data: Raw request payload
            schema_key: Key from SCHEMAS dict (e.g., "billing_upload")
            
        Returns:
            Validated + serialized dict (Decimals → floats for JSON)
            
        Raises:
            ValidationException: If validation fails
        """
        schema = SCHEMAS.get(schema_key)
        
        if schema is None:
            # No schema defined; return as-is (caller handles validation)
            return data
        
        if not isinstance(schema, type):
            # Schema not yet implemented
            return data
        
        try:
            # Validate + serialize
            validated = schema(**data)
            return validated.model_dump(mode="json")  # Converts Decimal → float
        except ValidationError as e:
            # Convert Pydantic errors to field:message dict
            errors = {}
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors[field] = error["msg"]
            raise ValidationException(
                message="Validation failed",
                errors=errors
            )