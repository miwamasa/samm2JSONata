"""Property matching engine for SAMM models."""

from typing import List, Tuple, Optional
import logging

from models import SAMMProperty, PropertyMapping

logger = logging.getLogger(__name__)


class PropertyMatcher:
    """Matches properties between source and target SAMM models."""

    # Matching method names and their confidence scores
    MATCHING_LEVELS = {
        "characteristic_match": 0.9,
        "preferred_name_match": 0.8,
        "property_uri_match": 0.7,
    }

    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize the property matcher.

        Args:
            confidence_threshold: Minimum confidence score for a match to be considered
        """
        self.confidence_threshold = confidence_threshold

    def match_properties(
        self,
        source_properties: List[SAMMProperty],
        target_properties: List[SAMMProperty],
    ) -> List[Tuple[SAMMProperty, SAMMProperty, str, float]]:
        """
        Match properties between source and target models.

        Args:
            source_properties: List of source properties
            target_properties: List of target properties

        Returns:
            List of tuples (source_prop, target_prop, method, confidence)
        """
        matches = []
        matched_targets = set()

        for source_prop in source_properties:
            best_match = None
            best_confidence = 0.0
            best_method = None

            for target_prop in target_properties:
                if target_prop.uri in matched_targets:
                    continue

                # Try matching methods in priority order
                match_result = self._find_best_match(source_prop, target_prop)
                if match_result:
                    method, confidence = match_result
                    if confidence > best_confidence:
                        best_match = target_prop
                        best_confidence = confidence
                        best_method = method

            # Add match if confidence meets threshold
            if (
                best_match
                and best_confidence >= self.confidence_threshold
            ):
                matches.append(
                    (source_prop, best_match, best_method, best_confidence)
                )
                matched_targets.add(best_match.uri)
                logger.info(
                    f"Matched {source_prop.local_name} -> {best_match.local_name} "
                    f"({best_method}, confidence: {best_confidence:.2f})"
                )

        logger.info(f"Total matches found: {len(matches)}")
        return matches

    def _find_best_match(
        self, source_prop: SAMMProperty, target_prop: SAMMProperty
    ) -> Optional[Tuple[str, float]]:
        """
        Find the best matching method and confidence for two properties.

        Returns:
            Tuple of (method_name, confidence) or None if no match
        """
        # Level 2: Characteristic match
        if self._characteristic_match(source_prop, target_prop):
            return ("characteristic_match", self.MATCHING_LEVELS["characteristic_match"])

        # Level 3: Preferred name match
        if self._preferred_name_match(source_prop, target_prop):
            return (
                "preferred_name_match",
                self.MATCHING_LEVELS["preferred_name_match"],
            )

        # Level 4: Property URI match (local name)
        if self._property_uri_match(source_prop, target_prop):
            return (
                "property_uri_match",
                self.MATCHING_LEVELS["property_uri_match"],
            )

        return None

    def _characteristic_match(
        self, source_prop: SAMMProperty, target_prop: SAMMProperty
    ) -> bool:
        """Check if characteristics match exactly."""
        if not source_prop.characteristic or not target_prop.characteristic:
            return False
        return source_prop.characteristic == target_prop.characteristic

    def _preferred_name_match(
        self, source_prop: SAMMProperty, target_prop: SAMMProperty
    ) -> bool:
        """Check if preferred names match (normalized)."""
        if not source_prop.preferred_name or not target_prop.preferred_name:
            return False

        # Normalize: lowercase, remove spaces and special characters
        source_normalized = self._normalize_name(source_prop.preferred_name)
        target_normalized = self._normalize_name(target_prop.preferred_name)

        return source_normalized == target_normalized

    def _property_uri_match(
        self, source_prop: SAMMProperty, target_prop: SAMMProperty
    ) -> bool:
        """Check if property local names match (case-insensitive)."""
        source_name = source_prop.local_name.lower()
        target_name = target_prop.local_name.lower()
        return source_name == target_name

    def _normalize_name(self, name: str) -> str:
        """
        Normalize a name for comparison.

        Removes spaces, special characters, converts to lowercase.
        """
        # Remove common words and connectors
        name = name.lower()
        # Remove parentheses and their contents
        import re

        name = re.sub(r"\([^)]*\)", "", name)
        # Remove special characters and spaces
        name = re.sub(r"[^a-z0-9]", "", name)
        return name
