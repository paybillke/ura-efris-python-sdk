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
        """
        schema = SCHEMAS.get(schema_key)
        
        if schema is None:
            return data
        
        if not isinstance(schema, type):
            return data
        
        try:
            validated = schema(**data)
            return validated.model_dump(mode="json")
        except ValidationError as e:
            errors = {}
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors[field] = error["msg"]
            
            raise ValidationException(
                message="Validation failed",
                errors=errors
            )