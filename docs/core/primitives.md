# Primitives

Tier 1 is the pure function layer. It owns deterministic data transformations
that other tiers can reuse.

```python
from extended_data.primitives import (
    decode_json,
    encode_yaml,
    normalize_data_encoding,
    number_to_words,
    redact_sensitive_text,
    string_to_bool,
    to_snake_case,
)

payload = decode_json('{"ServiceName": "API", "enabled": "true"}')
safe = redact_sensitive_text("Authorization: Bearer raw_token")

print(to_snake_case(payload["ServiceName"]))
print(string_to_bool(payload["enabled"]))
print(number_to_words(42))
print(normalize_data_encoding("YML"))
print(encode_yaml({"safe": safe}))
```

## Format Codecs

```python
from extended_data.primitives import decode_hcl2, decode_toml, decode_yaml
from extended_data.primitives import encode_hcl2, encode_json

terraform = {"locals": [{"region": "us-east-1"}]}
hcl_text = encode_hcl2(terraform)

assert decode_hcl2(hcl_text) == terraform
assert decode_yaml("service: api")["service"] == "api"
assert decode_toml("[service]\nname = 'api'")["service"]["name"] == "api"
print(encode_json({"service": "api"}, sort_keys=True))
```

Decode failures raise `DataDecodeError` through the public package surface. The
message includes format and position context without echoing raw payloads.

## Redaction

```python
from extended_data.primitives import redact_sensitive_data, redact_sensitive_text

print(redact_sensitive_text("failed for user@example.com", values=["user@example.com"]))
print(redact_sensitive_data({"token": "abc", "status": "ok"}))
```
