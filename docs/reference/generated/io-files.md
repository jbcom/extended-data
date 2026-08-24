---
title: io.files
description: Public API documentation generated from source.
---

# `io.files`

```python
class DataFile:
def get_parent_repository(file_path: FilePath | None = None, search_parent_directories: bool = True) -> Repo | None:
def get_repository_name(repo: Repo) -> str | None:
def clone_repository_to_temp(
def get_tld(file_path: FilePath | None = None, search_parent_directories: bool = True) -> Path | None:
def match_file_extensions(
def get_encoding_for_file_path(file_path: FilePath) -> str:
def file_path_depth(file_path: FilePath) -> int:
def file_path_rel_to_root(file_path: FilePath) -> str:
def resolve_local_path(file_path: FilePath, tld: Path | None = None) -> Path:
def is_url(path: str) -> bool:
def read_file(
def decode_file(
def read_data_file(
def write_file(
def delete_file(file_path: FilePath, tld: Path | None = None, missing_ok: bool = True) -> bool:
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/io/files.py)
