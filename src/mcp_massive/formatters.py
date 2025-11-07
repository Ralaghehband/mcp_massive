from __future__ import annotations

import json
import csv
import io
from typing import Any, List, Mapping, Sequence


def json_to_csv(json_input: str | Mapping[str, Any] | Sequence[Any]) -> str:
    """
    Convert JSON to flattened CSV format.

    Args:
        json_input: JSON string, mapping, or sequence. If the JSON has a 'results'
                   key containing a list, it will be extracted. Otherwise, the entire
                   structure will be wrapped in a list for processing.

    Returns:
        CSV string with headers and flattened rows
    """
    # Parse JSON if it's a string
    if isinstance(json_input, str):
        data = json.loads(json_input)
    else:
        data = json_input

    if isinstance(data, Mapping) and "results" in data:
        records = data["results"]
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        records = data
    else:
        records = [data]

    mapping_records: List[Mapping[str, Any]] = []
    for record in records:
        if isinstance(record, Mapping):
            mapping_records.append(record)
        else:
            mapping_records.append({"value": record})

    flattened_records = [_flatten_dict(record) for record in mapping_records]

    if not flattened_records:
        return ""

    # Get all unique keys across all records (for consistent column ordering)
    all_keys = []
    seen = set()
    for record in flattened_records:
        for key in record.keys():
            if key not in seen:
                all_keys.append(key)
                seen.add(key)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys, lineterminator="\n")
    writer.writeheader()
    writer.writerows(flattened_records)

    return output.getvalue()


def _flatten_dict(
    d: Mapping[str, Any], parent_key: str = "", sep: str = "_"
) -> dict[str, Any]:
    """
    Flatten a nested dictionary by joining keys with separator.

    Args:
        d: Dictionary to flatten
        parent_key: Key from parent level (for recursion)
        sep: Separator to use between nested keys

    Returns:
        Flattened dictionary with no nested structures
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, Mapping):
            # Recursively flatten nested dicts / mappings
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert lists to comma-separated strings
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))

    return dict(items)
