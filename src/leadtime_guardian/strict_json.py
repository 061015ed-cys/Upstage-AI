"""JSON trust boundary: reject duplicate keys, non-finite numbers and invalid UTF-8."""
import json
import math


def validate_json_value(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            validate_json_value(key)
            validate_json_value(item)
    elif isinstance(value, list):
        for item in value:
            validate_json_value(item)
    elif isinstance(value, str):
        value.encode("utf-8", errors="strict")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
    elif value is not None and not isinstance(value, (bool, int)):
        raise ValueError("unsupported JSON value type")


def loads_strict(text):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"nonstandard JSON number: {value}")

    if isinstance(text, bytes):
        text = text.decode("utf-8-sig", errors="strict")
    value = json.loads(text, object_pairs_hook=object_pairs, parse_constant=invalid_constant)
    validate_json_value(value)
    return value
