"""Main generator that orchestrates the transformation generation process."""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from parser import SAMMParser
from matcher import PropertyMatcher
from transformer import Transformer
from models import TransformationResult, SAMMProperty

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TransformationGenerator:
    """Main generator for SAMM to JSONata transformations."""

    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize the generator.

        Args:
            confidence_threshold: Minimum confidence for property matches
        """
        self.parser = SAMMParser()
        self.matcher = PropertyMatcher(confidence_threshold)
        self.transformer = Transformer()

    def generate(
        self, source_model_path: str, target_model_path: str, output_dir: str = "output"
    ) -> TransformationResult:
        """
        Generate transformation rules from source to target model.

        Args:
            source_model_path: Path to source SAMM model (TTL)
            target_model_path: Path to target SAMM model (TTL)
            output_dir: Directory to write output files

        Returns:
            TransformationResult object
        """
        logger.info("=" * 80)
        logger.info("SAMM to JSONata Transformation Generator")
        logger.info("=" * 80)

        # Parse models
        logger.info(f"Parsing source model: {source_model_path}")
        source_aspect = self.parser.parse_file(source_model_path)

        logger.info(f"Parsing target model: {target_model_path}")
        target_aspect = self.parser.parse_file(target_model_path)

        logger.info(f"Source properties: {len(source_aspect.properties)}")
        logger.info(f"Target properties: {len(target_aspect.properties)}")

        # Match properties
        logger.info("\nMatching properties...")
        matches = self.matcher.match_properties(
            source_aspect.properties, target_aspect.properties
        )

        # Create mappings with transformations
        logger.info("\nGenerating transformations...")
        mappings = []
        for source_prop, target_prop, method, confidence in matches:
            mapping = self.transformer.create_mapping(
                source_prop, target_prop, method, confidence
            )
            mappings.append(mapping)

        # Build complete transformation
        complete_transformation = self.transformer.build_complete_transformation(
            mappings
        )

        # Find unmapped properties
        unmapped = self._find_unmapped_properties(
            source_aspect.properties, target_aspect.properties, mappings
        )

        # Generate warnings
        warnings = self._generate_warnings(mappings, unmapped)

        # Create result
        result = TransformationResult(
            metadata={
                "generator": "SAMM-to-JSONata Generator v1.0",
                "generated_at": datetime.now().isoformat(),
                "source_model": str(Path(source_model_path).name),
                "target_model": str(Path(target_model_path).name),
                "source_aspect": source_aspect.preferred_name or source_aspect.local_name,
                "target_aspect": target_aspect.preferred_name or target_aspect.local_name,
                "mapping_confidence_avg": (
                    sum(m.confidence for m in mappings) / len(mappings)
                    if mappings
                    else 0.0
                ),
                "total_mappings": len(mappings),
                "source_properties_count": len(source_aspect.properties),
                "target_properties_count": len(target_aspect.properties),
            },
            mappings=mappings,
            complete_transformation=complete_transformation,
            unmapped_properties=unmapped,
            warnings=warnings,
        )

        # Write output files
        self._write_output(result, output_dir)

        logger.info("\n" + "=" * 80)
        logger.info("Generation complete!")
        logger.info(f"Mappings created: {len(mappings)}")
        logger.info(
            f"Unmapped source properties: {len(unmapped.get('source', []))}"
        )
        logger.info(
            f"Unmapped target properties: {len(unmapped.get('target', []))}"
        )
        logger.info(f"Warnings: {len(warnings)}")
        logger.info("=" * 80)

        return result

    def _find_unmapped_properties(
        self,
        source_properties: List[SAMMProperty],
        target_properties: List[SAMMProperty],
        mappings: List,
    ) -> Dict[str, List[str]]:
        """Find properties that weren't mapped."""
        mapped_source = {m.source_property.uri for m in mappings}
        mapped_target = {m.target_property.uri for m in mappings}

        unmapped_source = [
            p.local_name for p in source_properties if p.uri not in mapped_source
        ]
        unmapped_target = [
            p.local_name for p in target_properties if p.uri not in mapped_target
        ]

        return {"source": unmapped_source, "target": unmapped_target}

    def _generate_warnings(
        self, mappings: List, unmapped: Dict[str, List[str]]
    ) -> List[Dict[str, str]]:
        """Generate warnings for potential issues."""
        warnings = []

        # Warn about low confidence mappings
        for mapping in mappings:
            if mapping.confidence < 0.7:
                warnings.append(
                    {
                        "type": "low_confidence",
                        "property": f"{mapping.source_property.local_name} -> {mapping.target_property.local_name}",
                        "confidence": f"{mapping.confidence:.2f}",
                        "message": f"Mapping confidence below 0.7 ({mapping.confidence:.2f})",
                        "suggestion": "Manual review recommended",
                    }
                )

        # Warn about unmapped properties
        if unmapped["source"]:
            warnings.append(
                {
                    "type": "unmapped_source",
                    "count": str(len(unmapped["source"])),
                    "message": f"{len(unmapped['source'])} source properties could not be mapped",
                    "properties": ", ".join(unmapped["source"][:5])
                    + ("..." if len(unmapped["source"]) > 5 else ""),
                }
            )

        if unmapped["target"]:
            warnings.append(
                {
                    "type": "unmapped_target",
                    "count": str(len(unmapped["target"])),
                    "message": f"{len(unmapped['target'])} target properties were not mapped to",
                    "properties": ", ".join(unmapped["target"][:5])
                    + ("..." if len(unmapped["target"]) > 5 else ""),
                }
            )

        return warnings

    def _write_output(self, result: TransformationResult, output_dir: str):
        """Write output files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Write complete result as JSON
        result_file = output_path / "mapping_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            # Convert mappings to serializable format
            result_dict = {
                "metadata": result.metadata,
                "mappings": [
                    {
                        "source_property": m.source_property.local_name,
                        "source_preferred_name": m.source_property.preferred_name,
                        "target_property": m.target_property.local_name,
                        "target_preferred_name": m.target_property.preferred_name,
                        "mapping_method": m.mapping_method,
                        "confidence": m.confidence,
                        "transformation_type": m.transformation_type,
                        "jsonata_fragment": m.jsonata_fragment,
                    }
                    for m in result.mappings
                ],
                "complete_transformation": result.complete_transformation,
                "unmapped_properties": result.unmapped_properties,
                "warnings": result.warnings,
            }
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Wrote mapping result to: {result_file}")

        # Write JSONata transformation
        jsonata_file = output_path / "transformation.jsonata"
        with open(jsonata_file, "w", encoding="utf-8") as f:
            # Format as a JSONata expression
            f.write("/* Generated JSONata Transformation */\n")
            f.write(f"/* Source: {result.metadata['source_model']} */\n")
            f.write(f"/* Target: {result.metadata['target_model']} */\n")
            f.write(f"/* Generated: {result.metadata['generated_at']} */\n\n")
            f.write(json.dumps(result.complete_transformation, indent=2))

        logger.info(f"Wrote JSONata transformation to: {jsonata_file}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate JSONata transformations from SAMM models"
    )
    parser.add_argument(
        "--source", required=True, help="Path to source SAMM model (TTL)"
    )
    parser.add_argument(
        "--target", required=True, help="Path to target SAMM model (TTL)"
    )
    parser.add_argument(
        "--output", default="output", help="Output directory (default: output)"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.6,
        help="Minimum confidence threshold for matches (default: 0.6)",
    )

    args = parser.parse_args()

    generator = TransformationGenerator(confidence_threshold=args.confidence_threshold)
    generator.generate(args.source, args.target, args.output)


if __name__ == "__main__":
    main()
