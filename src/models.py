"""Data models for SAMM parsing and transformation."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SAMMProperty(BaseModel):
    """Represents a SAMM property with its metadata."""

    uri: str
    local_name: str
    preferred_name: Optional[str] = None
    description: Optional[str] = None
    characteristic: Optional[str] = None
    data_type: Optional[str] = None
    optional: bool = False
    payload_name: Optional[str] = None
    example_value: Optional[Any] = None
    unit: Optional[str] = None
    # Path in the JSON structure (e.g., "pcf.declaredUnitOfMeasurement")
    json_path: Optional[str] = None
    # Parent property name (for nested properties)
    parent_property: Optional[str] = None
    # Whether this property is a Collection (array in JSON)
    is_collection: bool = False
    # Whether this property is inside a collection element
    is_array_element: bool = False

    def __hash__(self):
        return hash(self.uri)

    def __eq__(self, other):
        if not isinstance(other, SAMMProperty):
            return False
        return self.uri == other.uri


class SAMMEntity(BaseModel):
    """Represents a SAMM entity with its properties."""

    uri: str
    local_name: str
    preferred_name: Optional[str] = None
    description: Optional[str] = None
    properties: List[SAMMProperty] = Field(default_factory=list)


class SAMMAspect(BaseModel):
    """Represents a SAMM aspect model."""

    uri: str
    local_name: str
    preferred_name: Optional[str] = None
    description: Optional[str] = None
    properties: List[SAMMProperty] = Field(default_factory=list)
    entities: Dict[str, SAMMEntity] = Field(default_factory=dict)


class PropertyMapping(BaseModel):
    """Represents a mapping between source and target properties."""

    source_property: SAMMProperty
    target_property: SAMMProperty
    mapping_method: str
    confidence: float
    transformation_type: str
    jsonata_fragment: str
    notes: Optional[str] = None


class TransformationResult(BaseModel):
    """Complete transformation result with metadata."""

    metadata: Dict[str, Any]
    mappings: List[PropertyMapping]
    complete_transformation: Dict[str, Any]
    unmapped_properties: Dict[str, List[str]]
    warnings: List[Dict[str, str]]
