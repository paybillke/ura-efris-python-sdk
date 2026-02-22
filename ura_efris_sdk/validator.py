"""
EFRIS Payload Validator
Validates request/response data against Pydantic schemas.
Provides detailed error messages for validation failures.
"""
from typing import Dict, Any, Optional, Type, List, Union
from pydantic import ValidationError, BaseModel, RootModel
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
    
    def _is_root_model(self, schema: Type) -> bool:
        """Check if schema is a Pydantic v2 RootModel"""
        return isinstance(schema, type) and issubclass(schema, RootModel)
    
    def _is_base_model(self, schema: Type) -> bool:
        """Check if schema is a Pydantic BaseModel"""
        return isinstance(schema, type) and issubclass(schema, BaseModel)
    
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
        
        try:
            # Handle RootModel schemas (lists)
            if self._is_root_model(schema):
                validated = schema(data)  # RootModel accepts data directly
                return validated.model_dump(mode="json", exclude_none=True)
            
            # Handle regular BaseModel schemas (objects)
            elif self._is_base_model(schema):
                validated = schema(**data)
                return validated.model_dump(mode="json", exclude_none=True)
            
            # Unknown schema type
            return data
            
        except ValidationError as e:
            raise self._format_validation_error(e)
        except Exception as e:
            raise ValidationException(
                message=f"Unexpected validation error: {str(e)}",
                errors={"_general": str(e)}
            )
    
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
        
        if schema is None:
            return response
        
        try:
            if self._is_root_model(schema):
                validated = schema(response)
                return validated.model_dump(mode="json", exclude_none=True)
            elif self._is_base_model(schema):
                validated = schema(**response)
                return validated.model_dump(mode="json", exclude_none=True)
        except ValidationError as e:
            # Log warning but don't fail
            error_msg = self._format_validation_error(e)
            print(f"⚠️  Response validation warning for {schema_key}: {error_msg.errors}")
        except Exception as e:
            print(f"⚠️  Response validation error for {schema_key}: {str(e)}")
        
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
            errors=errors,
            error_type="VALIDATION_ERROR"
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
        
        if schema is None:
            return None
        
        if self._is_root_model(schema):
            # For RootModel, get the inner type
            return {
                "__root__": {
                    "type": str(schema.__pydantic_generic_metadata__.get('args', ('unknown',))[0] 
                               if hasattr(schema, '__pydantic_generic_metadata__') else 'list'),
                    "required": True,
                    "description": "List of items"
                }
            }
        
        if self._is_base_model(schema):
            fields = {}
            for name, field_info in schema.model_fields.items():
                fields[name] = {
                    "type": str(field_info.annotation),
                    "required": field_info.is_required(),
                    "default": field_info.get_default() if not field_info.is_required() else None,
                    "description": field_info.description or ""
                }
            return fields
        
        return None
    
    def get_all_schema_keys(self) -> List[str]:
        """Get all available schema keys"""
        return list(SCHEMAS.keys())
    
    def validate_envelope(
        self, 
        envelope: Dict[str, Any], 
        interface_code: str
    ) -> Dict[str, Any]:
        """
        Validate full EFRIS envelope (data + globalInfo + returnStateInfo).
        
        Args:
            envelope: Full API envelope
            interface_code: T101, T109, etc.
        
        Returns:
            dict: Validated envelope
        """
        from .schemas import ApiEnvelope
        
        try:
            validated = ApiEnvelope(**envelope)
            return validated.model_dump(mode="json", exclude_none=True)
        except ValidationError as e:
            raise self._format_validation_error(e)