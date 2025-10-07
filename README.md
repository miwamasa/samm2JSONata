# SAMM to JSONata Transformation Generator

A tool to automatically generate JSONata transformation rules from SAMM (Semantic Aspect Meta Model) models.

## Overview

This tool analyzes two SAMM models (source and target) and automatically generates JSONata expressions to transform JSON instances from the source model format to the target model format.

### Key Features

- ✅ **Hierarchical Property Extraction**: Extracts 96+ properties from nested SAMM Entities
- ✅ **Semantic Matching**: Uses characteristic URIs and preferred names for intelligent matching
- ✅ **Multi-level Nesting**: Supports up to 3+ levels of nested structures
- ✅ **High Accuracy**: 96.9% mapping success rate with 0.90 average confidence
- ✅ **Standard Compliance**: Fully compliant with SAMM 2.1.0 specification

### What's New

**v2.0** - Major improvements:
- 🎯 **4x more properties extracted**: Now extracts nested Entity properties (96 vs 22 previously)
- 🏗️ **Full hierarchy support**: Correctly handles `pcf.dataQualityRating.technologicalDQR` paths
- 🔧 **SAMM compliant**: Respects `samm:payloadName` and Entity structures
- ✨ **Validated**: Tested with real PCF data, 100% value accuracy

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Generate Transformation Rules

```bash
python src/generator.py \
  --source test/pcf/Pcf.ttl \
  --target test/pcf/Pcf.ttl \
  --output output/
```

### Apply Transformation

```bash
python src/apply_transformation.py \
  --input test/pcf/Pcf.json \
  --transformation output/transformation.jsonata \
  --output output/transformed.json
```

## Documentation

- 📖 [Quick Start Guide](docs/quickstart.md) - Get started in 5 minutes
- 🎓 [Theory and Implementation](docs/theory_and_implementation.md) - Deep dive into algorithms
- 📋 [Specification](spec/specifcation.md) - Detailed transformation specification
- 📊 [Execution Report](output/transformation_summary.md) - Latest test results

## Project Structure

```
.
├── src/
│   ├── parser.py          # SAMM model parser
│   ├── matcher.py         # Property matching engine
│   ├── transformer.py     # Transformation type detector
│   ├── generator.py       # Main generator
│   └── validator.py       # Validation utilities
├── test/
│   ├── pcf/              # PCF test data
│   └── generic_digitalpassport/  # DPP test data
├── spec/
│   └── specifcation.md   # Detailed specification
└── output/               # Generated transformation rules
```

## Specification

See [spec/specifcation.md](spec/specifcation.md) for detailed specification of the transformation generation process.

## License

See individual SAMM model files for their respective licenses.
