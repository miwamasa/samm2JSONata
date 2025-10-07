"""Basic tests for the transformation generator."""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parser import SAMMParser
from matcher import PropertyMatcher
from transformer import Transformer
from generator import TransformationGenerator


def test_parser():
    """Test SAMM model parsing."""
    print("Testing SAMM parser...")

    parser = SAMMParser()

    # Parse PCF model
    pcf_aspect = parser.parse_file("test/pcf/Pcf.ttl")
    assert pcf_aspect is not None
    assert pcf_aspect.local_name == "Pcf"
    assert len(pcf_aspect.properties) > 0
    print(f"  ✓ Parsed PCF model: {len(pcf_aspect.properties)} properties")

    # Parse DPP model
    dpp_aspect = parser.parse_file(
        "test/generic_digitalpassport/DigitalProductPassport.ttl"
    )
    assert dpp_aspect is not None
    assert dpp_aspect.local_name == "DigitalProductPassport"
    assert len(dpp_aspect.properties) > 0
    print(f"  ✓ Parsed DPP model: {len(dpp_aspect.properties)} properties")


def test_matcher():
    """Test property matching."""
    print("\nTesting property matcher...")

    parser = SAMMParser()
    pcf_aspect = parser.parse_file("test/pcf/Pcf.ttl")
    dpp_aspect = parser.parse_file(
        "test/generic_digitalpassport/DigitalProductPassport.ttl"
    )

    matcher = PropertyMatcher(confidence_threshold=0.6)
    matches = matcher.match_properties(
        pcf_aspect.properties, dpp_aspect.properties
    )

    # PCF and DPP are different models, so matches may be 0
    print(f"  ✓ Found {len(matches)} matches (PCF vs DPP are different models)")

    # If there are matches, check that they have required fields
    if len(matches) > 0:
        for source_prop, target_prop, method, confidence in matches[:3]:
            assert source_prop.local_name
            assert target_prop.local_name
            assert method in ["characteristic_match", "preferred_name_match", "property_uri_match"]
            assert 0.0 <= confidence <= 1.0
            print(
                f"    {source_prop.local_name} -> {target_prop.local_name} "
                f"({method}, {confidence:.2f})"
            )
    else:
        print("    (No common properties between these models)")


def test_transformer():
    """Test transformation generation."""
    print("\nTesting transformer...")

    parser = SAMMParser()
    pcf_aspect = parser.parse_file("test/pcf/Pcf.ttl")
    dpp_aspect = parser.parse_file(
        "test/generic_digitalpassport/DigitalProductPassport.ttl"
    )

    matcher = PropertyMatcher(confidence_threshold=0.6)
    matches = matcher.match_properties(
        pcf_aspect.properties, dpp_aspect.properties
    )

    transformer = Transformer()
    mappings = []

    if len(matches) > 0:
        for source_prop, target_prop, method, confidence in matches[:5]:
            mapping = transformer.create_mapping(
                source_prop, target_prop, method, confidence
            )
            mappings.append(mapping)
            assert mapping.jsonata_fragment
            print(f"  ✓ {mapping.target_property.local_name}: {mapping.jsonata_fragment}")
    else:
        print("  ✓ No matches to transform (models are different)")

    # Build complete transformation
    complete = transformer.build_complete_transformation(mappings)
    assert isinstance(complete, dict)
    assert len(complete) == len(mappings)
    print(f"  ✓ Built complete transformation with {len(complete)} mappings")


def test_full_generation():
    """Test full generation process."""
    print("\nTesting full generation...")

    generator = TransformationGenerator(confidence_threshold=0.6)
    result = generator.generate(
        "test/pcf/Pcf.ttl",
        "test/generic_digitalpassport/DigitalProductPassport.ttl",
        "output",
    )

    # Metadata should always exist
    assert "total_mappings" in result.metadata
    assert isinstance(result.complete_transformation, dict)

    print(f"  ✓ Generated {result.metadata['total_mappings']} mappings")
    if result.metadata['total_mappings'] > 0:
        print(
            f"  ✓ Average confidence: {result.metadata['mapping_confidence_avg']:.2f}"
        )
    print(f"  ✓ Warnings: {len(result.warnings)}")

    # Check output files exist
    output_dir = Path("output")
    assert (output_dir / "mapping_result.json").exists()
    assert (output_dir / "transformation.jsonata").exists()
    print("  ✓ Output files created successfully")


def test_transformation_structure():
    """Test that transformation output has correct structure."""
    print("\nTesting transformation output structure...")

    with open("output/mapping_result.json", "r") as f:
        result = json.load(f)

    # Check metadata
    assert "metadata" in result
    assert "generator" in result["metadata"]
    assert "generated_at" in result["metadata"]
    assert "mapping_confidence_avg" in result["metadata"]

    # Check mappings
    assert "mappings" in result
    # Mappings can be empty if models are different

    if len(result["mappings"]) > 0:
        for mapping in result["mappings"][:3]:
            assert "source_property" in mapping
            assert "target_property" in mapping
            assert "mapping_method" in mapping
            assert "confidence" in mapping
            assert "transformation_type" in mapping
            assert "jsonata_fragment" in mapping

    # Check complete transformation
    assert "complete_transformation" in result
    assert isinstance(result["complete_transformation"], dict)

    # Check unmapped properties
    assert "unmapped_properties" in result
    assert "source" in result["unmapped_properties"]
    assert "target" in result["unmapped_properties"]

    # Check warnings
    assert "warnings" in result

    print("  ✓ All required fields present")
    print("  ✓ Structure is valid")


if __name__ == "__main__":
    print("=" * 80)
    print("Running SAMM to JSONata Generator Tests")
    print("=" * 80)

    try:
        test_parser()
        test_matcher()
        test_transformer()
        test_full_generation()
        test_transformation_structure()

        print("\n" + "=" * 80)
        print("All tests passed! ✓")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
