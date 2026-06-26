# Logging

Structured lifecycle logging is now exposed from `extended_data.logging` and the
package root.

```python
from extended_data import Logging

logger = Logging(logger_name="pipeline")
logger.info("starting", data={"service": "api"})
logger.warning("retrying", data={"attempt": 2})
```

Logging helpers share the package's data-lowering and redaction behavior. When
messages include JSON-like payloads, secret-like keys and known caller-provided
values can be withheld before output.

```python
from extended_data import Logging
from extended_data.primitives import redact_sensitive_data

logger = Logging(logger_name="safe")
payload = redact_sensitive_data({"token": "abc", "status": "ok"})
logger.info("connector response", data=payload)
```
