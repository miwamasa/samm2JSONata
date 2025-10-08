"""Transformation type detection and JSONata expression generation."""

from typing import List, Dict, Any
import logging

from models import SAMMProperty, PropertyMapping

logger = logging.getLogger(__name__)


class Transformer:
    """Determines transformation types and generates JSONata expressions."""

    # XSD type mapping to JSONata functions
    TYPE_CAST_MAP = {
        "string": "$string",
        "integer": "$number",
        "int": "$number",
        "float": "$number",
        "double": "$number",
        "decimal": "$number",
        "boolean": "$boolean",
        "nonNegativeInteger": "$number",
        "positiveInteger": "$number",
    }

    def __init__(self):
        pass

    def create_mapping(
        self,
        source_prop: SAMMProperty,
        target_prop: SAMMProperty,
        method: str,
        confidence: float,
    ) -> PropertyMapping:
        """
        Create a property mapping with transformation details.

        Args:
            source_prop: Source property
            target_prop: Target property
            method: Matching method used
            confidence: Confidence score

        Returns:
            PropertyMapping object
        """
        transformation_type = self._determine_transformation_type(
            source_prop, target_prop
        )
        jsonata_fragment = self._generate_jsonata_expression(
            source_prop, target_prop, transformation_type
        )

        return PropertyMapping(
            source_property=source_prop,
            target_property=target_prop,
            mapping_method=method,
            confidence=confidence,
            transformation_type=transformation_type,
            jsonata_fragment=jsonata_fragment,
        )

    def _determine_transformation_type(
        self, source_prop: SAMMProperty, target_prop: SAMMProperty
    ) -> str:
        """
        Determine what type of transformation is needed.

        Returns:
            Transformation type: "direct", "type_cast", or "structure_transform"
        """
        # Check if data types differ
        if source_prop.data_type and target_prop.data_type:
            source_type = self._normalize_type(source_prop.data_type)
            target_type = self._normalize_type(target_prop.data_type)

            if source_type != target_type:
                # Check if types are compatible for casting
                if self._can_cast(source_type, target_type):
                    return "type_cast"
                else:
                    logger.warning(
                        f"Cannot cast {source_type} to {target_type} "
                        f"for {source_prop.local_name} -> {target_prop.local_name}"
                    )

        # If characteristics differ significantly, might need structure transform
        if source_prop.characteristic and target_prop.characteristic:
            if source_prop.characteristic != target_prop.characteristic:
                # Check if one is a collection and the other isn't
                source_is_collection = self._is_collection_characteristic(
                    source_prop.characteristic
                )
                target_is_collection = self._is_collection_characteristic(
                    target_prop.characteristic
                )
                if source_is_collection != target_is_collection:
                    return "structure_transform"

        # Default to direct mapping
        return "direct"

    def _generate_jsonata_expression(
        self,
        source_prop: SAMMProperty,
        target_prop: SAMMProperty,
        transformation_type: str,
    ) -> str:
        """
        Generate JSONata expression for the transformation.

        Args:
            source_prop: Source property
            target_prop: Target property
            transformation_type: Type of transformation needed

        Returns:
            JSONata expression string
        """
        # Determine the source path (use json_path if available, otherwise construct it)
        if source_prop.json_path:
            source_path = source_prop.json_path
        else:
            source_path = source_prop.payload_name or source_prop.local_name

        # Handle array elements based on source and target types
        if source_prop.is_array_element and source_prop.parent_property:
            # Determine if we need array indexing
            # Case 1: source is array element, target is also array element -> map all elements
            # Case 2: source is array element, target is NOT array element -> take first element [0]

            if not target_prop.is_array_element:
                # Array to single: take first element
                parts = source_path.split(".")
                parent_name = source_prop.parent_property

                # Find where the parent property is in the path
                for i, part in enumerate(parts):
                    if part == parent_name:
                        # Insert [0] after this part
                        parts[i] = f"{part}[0]"
                        break

                source_path = ".".join(parts)
            # else: both are array elements, map entire arrays (no [0] needed)

        # Base expression
        base_expr = f"$.{source_path}"

        if transformation_type == "direct":
            return base_expr

        elif transformation_type == "type_cast":
            # Apply type casting function
            target_type = self._normalize_type(target_prop.data_type)
            cast_function = self.TYPE_CAST_MAP.get(target_type)
            if cast_function:
                return f"{cast_function}({base_expr})"
            else:
                logger.warning(
                    f"No cast function for type {target_type}, using direct mapping"
                )
                return base_expr

        elif transformation_type == "structure_transform":
            # Handle structure transformations including array conversions
            if source_prop.is_array_element and not target_prop.is_array_element:
                # Already handled above with [0]
                return base_expr
            elif not source_prop.is_array_element and target_prop.is_array_element:
                # Single to array: wrap in array
                logger.info(
                    f"Wrapping single value in array for {source_prop.local_name} -> {target_prop.local_name}"
                )
                return f"[{base_expr}]"
            else:
                logger.info(
                    f"Structure transform needed for {source_prop.local_name}, "
                    "using direct mapping for now"
                )
                return base_expr

        return base_expr

    def _normalize_type(self, data_type: str) -> str:
        """
        Normalize XSD data type to a simple type name.

        Args:
            data_type: Full XSD type URI

        Returns:
            Simplified type name (e.g., "string", "integer")
        """
        # Extract type from XSD URI
        if "#" in data_type:
            type_name = data_type.split("#")[-1]
        elif "/" in data_type:
            type_name = data_type.split("/")[-1]
        else:
            type_name = data_type

        return type_name.lower()

    def _can_cast(self, source_type: str, target_type: str) -> bool:
        """
        Check if source type can be cast to target type.

        Args:
            source_type: Source type name
            target_type: Target type name

        Returns:
            True if casting is possible
        """
        # Numeric types can be cast to each other
        numeric_types = {
            "integer",
            "int",
            "float",
            "double",
            "decimal",
            "nonnegativeinteger",
            "positiveinteger",
        }

        if source_type in numeric_types and target_type in numeric_types:
            return True

        # String can be cast to most types
        if source_type == "string":
            return True

        # Most types can be cast to string
        if target_type == "string":
            return True

        # Boolean conversions
        if source_type == "boolean" or target_type == "boolean":
            return True

        return False

    def _is_collection_characteristic(self, characteristic: str) -> bool:
        """
        Check if a characteristic represents a collection (List, Set, etc.).

        Args:
            characteristic: Characteristic URI

        Returns:
            True if it's a collection type
        """
        collection_types = ["List", "Set", "Collection", "SortedSet"]
        return any(ct in characteristic for ct in collection_types)

    def build_complete_transformation(
        self, mappings: List[PropertyMapping]
    ) -> Dict[str, Any]:
        """
        Build the complete JSONata transformation object.

        Args:
            mappings: List of property mappings

        Returns:
            Dictionary representing the complete transformation
        """
        transformation = {}

        for mapping in mappings:
            target_prop = mapping.target_property
            # Use json_path if available for nested properties
            if target_prop.json_path:
                target_path = target_prop.json_path
            else:
                target_path = target_prop.payload_name or target_prop.local_name

            # Build nested structure
            self._set_nested_path(transformation, target_path, mapping.jsonata_fragment)

        return transformation

    def _set_nested_path(self, obj: Dict, path: str, value: Any):
        """
        Set a value in a nested dictionary using a dot-separated path.

        Args:
            obj: Dictionary to modify
            path: Dot-separated path (e.g., "pcf.declaredUnitOfMeasurement")
            value: Value to set
        """
        keys = path.split(".")
        current = obj

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # If the key exists but is not a dict, we need to convert it
                # This happens when a parent property is mapped before its children
                logger.warning(
                    f"Overwriting non-dict value at '{key}' to add nested property"
                )
                current[key] = {}
            current = current[key]

        # Only set if the final key doesn't exist or is being overwritten intentionally
        if keys[-1] not in current or not isinstance(current.get(keys[-1]), dict):
            current[keys[-1]] = value
        else:
            # The key already has nested children, don't overwrite
            logger.warning(
                f"Skipping value assignment for '{path}' as it already has nested children"
            )
