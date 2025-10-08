"""Apply JSONata transformation to JSON data."""

import json
import argparse
from pathlib import Path


def json_to_jsonata_expr(obj, indent=0):
    """
    Convert a JSON object with JSONata expression strings to a JSONata expression.

    Args:
        obj: JSON object (dict, list, or string)
        indent: Current indentation level

    Returns:
        String representation of JSONata expression
    """
    if isinstance(obj, dict):
        if not obj:
            return "{}"

        indent_str = "  " * indent
        next_indent_str = "  " * (indent + 1)
        items = []

        for key, value in obj.items():
            value_expr = json_to_jsonata_expr(value, indent + 1)
            items.append(f'{next_indent_str}"{key}": {value_expr}')

        return "{\n" + ",\n".join(items) + f"\n{indent_str}}}"

    elif isinstance(obj, list):
        if not obj:
            return "[]"

        indent_str = "  " * indent
        next_indent_str = "  " * (indent + 1)
        items = []

        for item in obj:
            item_expr = json_to_jsonata_expr(item, indent + 1)
            items.append(f"{next_indent_str}{item_expr}")

        return "[\n" + ",\n".join(items) + f"\n{indent_str}]"

    elif isinstance(obj, str):
        # If it's a JSONata expression (starts with $), use it as-is
        if obj.startswith("$"):
            return obj
        # Otherwise, it's a string literal
        return json.dumps(obj)

    elif isinstance(obj, (int, float, bool)) or obj is None:
        return json.dumps(obj)

    else:
        return json.dumps(obj)


def apply_transformation_manually(source_data, transformation_map):
    """
    Manually apply transformation by evaluating JSONata paths.

    Args:
        source_data: Source JSON data
        transformation_map: Transformation mapping

    Returns:
        Transformed data
    """
    def evaluate_path(data, path):
        """
        Evaluate a JSONata path.

        Supports:
        - $.field - simple property access
        - $.array[0].field - array element access
        - $.array.field - map over all array elements (returns array)
        """
        if not path.startswith("$."):
            return path

        # Remove the $. prefix
        path = path[2:]

        # Split by dots and navigate
        parts = path.split(".")
        current = data

        for i, part in enumerate(parts):
            # Check if this part contains an array index like "array[0]"
            if "[" in part and "]" in part:
                # Extract the property name and index
                prop_name = part[:part.index("[")]
                index_str = part[part.index("[") + 1:part.index("]")]

                try:
                    index = int(index_str)
                    # Navigate to the property first
                    if isinstance(current, dict) and prop_name in current:
                        current = current[prop_name]
                        # Then access the array element
                        if isinstance(current, list) and 0 <= index < len(current):
                            current = current[index]
                        else:
                            return None
                    else:
                        return None
                except (ValueError, IndexError):
                    return None
            else:
                # Normal property access
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list):
                    # Array mapping: apply remaining path to each element
                    remaining_parts = parts[i:]
                    remaining_path = ".".join(remaining_parts)

                    result = []
                    for item in current:
                        item_current = item
                        for sub_part in remaining_parts:
                            if isinstance(item_current, dict) and sub_part in item_current:
                                item_current = item_current[sub_part]
                            else:
                                item_current = None
                                break
                        if item_current is not None:
                            result.append(item_current)

                    return result if result else None
                else:
                    return None

        return current

    def process_value(value):
        """Process a transformation value (could be a path or nested object)"""
        if isinstance(value, str):
            return evaluate_path(source_data, value)
        elif isinstance(value, dict):
            result = {}
            for k, v in value.items():
                result[k] = process_value(v)
            return result
        elif isinstance(value, list):
            return [process_value(item) for item in value]
        else:
            return value

    return process_value(transformation_map)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Apply JSONata transformation to JSON data"
    )
    parser.add_argument(
        "--input", required=True, help="Input JSON file"
    )
    parser.add_argument(
        "--transformation", required=True, help="Transformation JSON file"
    )
    parser.add_argument(
        "--output", required=True, help="Output JSON file"
    )
    parser.add_argument(
        "--expr-output", help="Output JSONata expression file (optional)"
    )

    args = parser.parse_args()

    # Read input data
    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    print(f"Loaded input data from {args.input}")

    # Read transformation
    with open(args.transformation, "r", encoding="utf-8") as f:
        # Skip comment lines
        lines = f.readlines()
        json_lines = [line for line in lines if not line.strip().startswith("/*")]
        transformation_json = "".join(json_lines)
        transformation = json.loads(transformation_json)

    print(f"Loaded transformation from {args.transformation}")

    # Generate JSONata expression if requested
    if args.expr_output:
        jsonata_expr = json_to_jsonata_expr(transformation)
        with open(args.expr_output, "w", encoding="utf-8") as f:
            f.write(jsonata_expr)
        print(f"Generated JSONata expression: {args.expr_output}")

    # Apply transformation manually
    print("\nApplying transformation...")
    result = apply_transformation_manually(input_data, transformation)

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Wrote transformed data to {args.output}")

    # Print summary
    def count_properties(obj):
        if isinstance(obj, dict):
            return len(obj) + sum(count_properties(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(count_properties(item) for item in obj)
        else:
            return 0

    input_props = count_properties(input_data)
    output_props = count_properties(result)

    print(f"\nSummary:")
    print(f"  Input properties: {input_props}")
    print(f"  Output properties: {output_props}")


if __name__ == "__main__":
    main()
