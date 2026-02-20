"""
EFRIS Payload Validator
Validates request/response data against Pydantic schemas.
Provides detailed error messages for validation failures.
"""
from typing import Dict, Any, Optional, Type
from pydantic import ValidationError, BaseModel
import json
from .schemas import SCHEMAS
from .exceptions import ValidationException


class Validator:
    """
    Validates data against Pydantic schemas defined in schemas.py.
    
    Features:
        - Request validation before API calls
        - Response validation (warnings only)
        - Detailed field-level error messages
        - Support for list and object schemas
    """
    
    def validate(self, data: Dict[str, Any], schema_key: str) -> Dict[str, Any]:
        """
        Validate request data against schema.
        
        Args:
            data: Data to validate
            schema_key: Schema name from SCHEMAS dict
        
        Returns:
            dict: Validated data (with defaults applied)
        
        Raises:
            ValidationException: If validation fails
        """
        schema = SCHEMAS.get(schema_key)
        
        # No schema defined - return data as-is
        if schema is None:
            return data
        
        # Handle list schemas (RootModel)
        if isinstance(data, list):
            if hasattr(schema, "__root__"):
                try:
                    validated = schema(__root__=data)
                    return validated.__root__
                except ValidationError as e:
                    raise self._format_validation_error(e)
            
            # List of model instances
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                try:
                    return [
                        schema(**item).model_dump(mode="json")
                        for item in data
                    ]
                except ValidationError as e:
                    raise self._format_validation_error(e)
        
        # Handle object schemas
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                validated = schema(**data)
                return validated.model_dump(mode="json", exclude_none=True)
            except ValidationError as e:
                raise self._format_validation_error(e)
        
        return data
    
    def validate_response(
        self,
        response: Dict[str, Any],
        schema_key: str
    ) -> Dict[str, Any]:
        """
        Validate response data against schema (non-blocking).
        
        Args:
            response: Response data to validate
            schema_key: Schema name
        
        Returns:
            dict: Response data (unchanged if validation fails)
        
        Note: Response validation only logs warnings, doesn't raise exceptions.
        """
        schema = SCHEMAS.get(schema_key)
        
        if schema is None or not isinstance(schema, type):
            return response
        
        try:
            if isinstance(response, list) and hasattr(schema, "__root__"):
                validated = schema(__root__=response)
                return validated.__root__
            elif isinstance(schema, type):
                validated = schema(**response)
                return validated.model_dump(mode="json")
        except ValidationError as e:
            # Log warning but don't fail
            print(f"Response validation warning for {schema_key}: {e}")
        
        return response
    
    def _format_validation_error(self, error: ValidationError) -> ValidationException:
        """
        Format Pydantic ValidationError into ValidationException.
        
        Args:
            error: Pydantic ValidationError
        
        Returns:
            ValidationException: Formatted exception with field errors
        """
        errors = {}
        for err in error.errors():
            # Build field path: ['goodsDetails', 0, 'qty'] -> "goodsDetails.0.qty"
            field_path = ".".join(str(loc) for loc in err["loc"])
            errors[field_path] = err["msg"]
        
        return ValidationException(
            message="Payload validation failed",
            errors=errors
        )
    
    def get_schema_fields(self, schema_key: str) -> Optional[Dict[str, Any]]:
        """
        Get schema field definitions for documentation.
        
        Args:
            schema_key: Schema name
        
        Returns:
            dict: Field definitions with types and requirements
        """
        schema = SCHEMAS.get(schema_key)
        
        if schema is None or not isinstance(schema, type):
            return None
        
        fields = {}
        for name, field_info in schema.model_fields.items():
            fields[name] = {
                "type": str(field_info.annotation),
                "required": field_info.is_required(),
                "description": field_info.description or ""
            }
        
        return fields