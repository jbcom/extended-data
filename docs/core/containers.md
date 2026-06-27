# Containers

Tier 2 wraps Python data shapes with the generic `ExtendedData` facade plus
shape-specific `ExtendedString`, `ExtendedDict`, `ExtendedList`,
`ExtendedTuple`, and `ExtendedSet` containers. Construction and mutation promote
nested values, so method chains survive normal Python literals.

```python
from extended_data import ExtendedData, ExtendedDict, ExtendedList, ExtendedString

payload = ExtendedDict({"service": {"name": "api"}, "tags": ["api", "api", ""]})
generic = ExtendedData(payload).merge({"service": {"enabled": True}})

print(payload["service"]["name"].upper_first())
print(generic.as_builtin()["service"]["enabled"])
print(payload["tags"].compact().deduplicate())
print(ExtendedString("HTTP Response Value").to_snake_case())
```

## Promotion and Lowering

```python
from extended_data import extend_data, to_builtin

data = extend_data({"outer": {"inner": ["api"]}})
assert data["outer"]["inner"][0].upper_first() == "Api"

plain = to_builtin(data)
assert plain == {"outer": {"inner": ["api"]}}
```

Tuples remain tuple-shaped when promoted and lowered. Sets stay set-shaped.
Mapping keys are lowered before export so JSON, YAML, TOML, and HCL encoders can
hand data to their underlying format libraries safely.
