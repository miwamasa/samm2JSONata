"""SAMM model parser using RDFLib."""

from typing import Dict, List, Optional, Tuple
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import logging

from models import SAMMProperty, SAMMEntity, SAMMAspect

# SAMM namespaces
SAMM = Namespace("urn:samm:org.eclipse.esmf.samm:meta-model:2.1.0#")
SAMM_C = Namespace("urn:samm:org.eclipse.esmf.samm:characteristic:2.1.0#")
SAMM_E = Namespace("urn:samm:org.eclipse.esmf.samm:entity:2.1.0#")
UNIT = Namespace("urn:samm:org.eclipse.esmf.samm:unit:2.1.0#")

logger = logging.getLogger(__name__)


class SAMMParser:
    """Parser for SAMM models in Turtle format."""

    def __init__(self):
        self.graph = Graph()

    def parse_file(self, file_path: str) -> SAMMAspect:
        """
        Parse a SAMM model from a TTL file.

        Args:
            file_path: Path to the TTL file

        Returns:
            SAMMAspect object containing the parsed model
        """
        logger.info(f"Parsing SAMM model from {file_path}")
        # Create a new graph for each file to avoid mixing models
        self.graph = Graph()
        self.graph.parse(file_path, format="turtle")

        # Find the Aspect (there should be one per file)
        aspect_uri = self._find_aspect()
        if not aspect_uri:
            raise ValueError("No Aspect found in the model")

        aspect = self._parse_aspect(aspect_uri)
        logger.info(f"Successfully parsed aspect: {aspect.preferred_name}")

        return aspect

    def _find_aspect(self) -> Optional[URIRef]:
        """Find the Aspect URI in the graph."""
        for s, p, o in self.graph.triples((None, RDF.type, SAMM.Aspect)):
            return s
        return None

    def _parse_aspect(self, aspect_uri: URIRef) -> SAMMAspect:
        """Parse an Aspect and its properties."""
        aspect = SAMMAspect(
            uri=str(aspect_uri),
            local_name=self._get_local_name(aspect_uri),
            preferred_name=self._get_preferred_name(aspect_uri),
            description=self._get_description(aspect_uri),
        )

        # Parse properties
        properties = self._get_properties(aspect_uri)
        aspect.properties = [
            self._parse_property(prop_uri, prop_info)
            for prop_uri, prop_info in properties
        ]

        # Set json_path for top-level properties
        for prop in aspect.properties:
            if not prop.json_path:
                prop.json_path = prop.payload_name or prop.local_name

        # Parse entities referenced by properties and extract nested properties
        all_properties = list(aspect.properties)  # Start with top-level properties

        for prop in aspect.properties:
            if prop.characteristic:
                entity_uri = self._get_entity_from_characteristic(
                    URIRef(prop.characteristic)
                )
                if entity_uri:
                    # Parse the entity
                    if entity_uri not in aspect.entities:
                        entity = self._parse_entity(entity_uri)
                        aspect.entities[str(entity_uri)] = entity
                    else:
                        entity = aspect.entities[str(entity_uri)]

                    # Extract entity properties as nested properties
                    parent_path = prop.payload_name or prop.local_name
                    nested_props = self._extract_nested_properties(
                        entity, parent_path, prop.local_name, prop.is_collection
                    )
                    all_properties.extend(nested_props)

        # Update the properties list to include nested properties
        aspect.properties = all_properties

        return aspect

    def _parse_property(
        self, property_uri: URIRef, property_info: Dict
    ) -> SAMMProperty:
        """Parse a single property."""
        prop = SAMMProperty(
            uri=str(property_uri),
            local_name=self._get_local_name(property_uri),
            preferred_name=self._get_preferred_name(property_uri),
            description=self._get_description(property_uri),
            optional=property_info.get("optional", False),
            payload_name=property_info.get("payloadName"),
        )

        # Get characteristic
        characteristic = self.graph.value(property_uri, SAMM.characteristic)
        if characteristic:
            prop.characteristic = str(characteristic)

            # Check if this is a collection
            prop.is_collection = self._is_collection_characteristic(characteristic)

        # Get data type (might be on the characteristic or property itself)
        data_type = self.graph.value(property_uri, SAMM.dataType)
        if not data_type and characteristic:
            data_type = self.graph.value(characteristic, SAMM.dataType)
        if data_type:
            prop.data_type = str(data_type)

        # Get example value
        example = self.graph.value(property_uri, SAMM.exampleValue)
        if example:
            prop.example_value = str(example)

        return prop

    def _parse_entity(self, entity_uri: URIRef) -> SAMMEntity:
        """Parse an entity and its properties."""
        entity = SAMMEntity(
            uri=str(entity_uri),
            local_name=self._get_local_name(entity_uri),
            preferred_name=self._get_preferred_name(entity_uri),
            description=self._get_description(entity_uri),
        )

        # Parse entity properties
        properties = self._get_properties(entity_uri)
        entity.properties = [
            self._parse_property(prop_uri, prop_info)
            for prop_uri, prop_info in properties
        ]

        return entity

    def _get_properties(self, subject_uri: URIRef) -> List[Tuple[URIRef, Dict]]:
        """
        Get properties from an Aspect or Entity.

        Returns list of (property_uri, property_info_dict) tuples.
        """
        properties = []

        # Get the properties list (samm:properties is an RDF list)
        props_list = self.graph.value(subject_uri, SAMM.properties)
        if props_list:
            items = list(self.graph.items(props_list))
            for item in items:
                # Each item can be either a direct property URI or a blank node with metadata
                if isinstance(item, URIRef):
                    # Direct property reference
                    prop_uri = item
                    properties.append((prop_uri, {}))
                else:
                    # Blank node with property metadata
                    prop_uri = self.graph.value(item, SAMM.property)
                    if prop_uri:
                        prop_info = {}

                        # Check if optional
                        optional = self.graph.value(item, SAMM.optional)
                        if optional:
                            prop_info["optional"] = str(optional).lower() == "true"

                        # Get payload name
                        payload_name = self.graph.value(item, SAMM.payloadName)
                        if payload_name:
                            prop_info["payloadName"] = str(payload_name)

                        properties.append((prop_uri, prop_info))

        return properties

    def _is_collection_characteristic(
        self, characteristic_uri: URIRef
    ) -> bool:
        """Check if a characteristic is a Collection type."""
        # Get the type of the characteristic
        char_type = self.graph.value(characteristic_uri, RDF.type)
        if char_type:
            # Check if it's a Collection or its subtypes (Set, List, SortedSet, TimeSeries)
            collection_types = [
                SAMM_C.Collection,
                SAMM_C.Set,
                SAMM_C.List,
                SAMM_C.SortedSet,
                SAMM_C.TimeSeries,
            ]
            if char_type in collection_types:
                return True
        return False

    def _get_entity_from_characteristic(
        self, characteristic_uri: URIRef
    ) -> Optional[URIRef]:
        """Get the entity URI from a characteristic if it's a SingleEntity or collection."""
        # Check if it's a SingleEntity or Collection
        entity = self.graph.value(characteristic_uri, SAMM.dataType)
        if entity:
            # Check if this is an entity (not a primitive type like xsd:string)
            if not str(entity).startswith("http://www.w3.org/2001/XMLSchema"):
                # Check if it's defined as an Entity
                entity_type = self.graph.value(entity, RDF.type)
                if entity_type == SAMM.Entity:
                    return entity
        return None

    def _get_preferred_name(self, subject: URIRef) -> Optional[str]:
        """Get the preferred name (in English if available)."""
        for obj in self.graph.objects(subject, SAMM.preferredName):
            if isinstance(obj, Literal):
                if obj.language == "en" or obj.language is None:
                    return str(obj)
        return None

    def _get_description(self, subject: URIRef) -> Optional[str]:
        """Get the description (in English if available)."""
        for obj in self.graph.objects(subject, SAMM.description):
            if isinstance(obj, Literal):
                if obj.language == "en" or obj.language is None:
                    return str(obj)
        return None

    def _get_local_name(self, uri: URIRef) -> str:
        """Extract the local name from a URI."""
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        elif "/" in uri_str:
            return uri_str.split("/")[-1]
        return uri_str

    def _extract_nested_properties(
        self,
        entity: SAMMEntity,
        parent_path: str,
        parent_name: str,
        parent_is_collection: bool = False,
    ) -> List[SAMMProperty]:
        """
        Extract properties from an entity as nested properties.

        Args:
            entity: The entity containing the properties
            parent_path: The JSON path to the parent property (e.g., "pcf")
            parent_name: The name of the parent property
            parent_is_collection: Whether the parent property is a collection

        Returns:
            List of properties with json_path and parent_property set
        """
        nested_properties = []

        for entity_prop in entity.properties:
            # Create a copy with updated path information
            nested_prop = SAMMProperty(
                uri=entity_prop.uri,
                local_name=entity_prop.local_name,
                preferred_name=entity_prop.preferred_name,
                description=entity_prop.description,
                characteristic=entity_prop.characteristic,
                data_type=entity_prop.data_type,
                optional=entity_prop.optional,
                payload_name=entity_prop.payload_name,
                example_value=entity_prop.example_value,
                unit=entity_prop.unit,
                # Set the JSON path
                json_path=f"{parent_path}.{entity_prop.payload_name or entity_prop.local_name}",
                parent_property=parent_name,
                is_collection=entity_prop.is_collection,
                is_array_element=parent_is_collection,  # Mark if inside a collection
            )
            nested_properties.append(nested_prop)

            # Recursively extract nested entity properties
            if nested_prop.characteristic:
                nested_entity_uri = self._get_entity_from_characteristic(
                    URIRef(nested_prop.characteristic)
                )
                if nested_entity_uri:
                    nested_entity = self._parse_entity(nested_entity_uri)
                    deeper_nested_props = self._extract_nested_properties(
                        nested_entity,
                        nested_prop.json_path,
                        nested_prop.local_name,
                        nested_prop.is_collection,  # Pass collection flag
                    )
                    nested_properties.extend(deeper_nested_props)

        return nested_properties
