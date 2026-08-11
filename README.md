# OpenAPI Utils

Small Python utilities for transforming OpenAPI documents.

## Remove selected operations

`remove_openapi_operations()` removes selected operations from an OpenAPI document and then removes components that are no longer reachable from the remaining document.

```python
from openapi_utils import remove_openapi_operations

result = remove_openapi_operations(
    document,
    [
        ("/users", "POST"),
        ("/orders/{id}", "DELETE"),
    ],
)
```

## Keep only selected operations

`keep_openapi_operations()` does the inverse: it keeps only the operations you explicitly list and removes all other paths and HTTP operations.

```python
from openapi_utils import keep_openapi_operations

result = keep_openapi_operations(
    document,
    [
        ("/users", "GET"),
        ("/orders/{id}", "DELETE"),
    ],
)
```

### `all` method

Use `"all"` when every existing HTTP operation for a path should be preserved.

```python
result = keep_openapi_operations(
    document,
    [
        ("/users", "GET"),
        ("/health", "all"),
    ],
)
```

In this example:

- only `GET /users` is kept for `/users`;
- every HTTP method currently defined for `/health` is kept;
- all other paths are removed.

`all` is case-insensitive, just like normal HTTP methods.

Path-level metadata such as `parameters`, `summary`, `description`, `servers`, and `$ref` is preserved for paths that remain.

## Component pruning

After either filtering operation, unused entries under `components` are removed automatically.

The important part is that shared components are preserved.

For example, if both `GET /users` and `POST /users` reference `#/components/schemas/User`, removing `POST /users` or keeping only `GET /users` will **not** remove `User`, because the remaining operation still uses it.

The pruning algorithm follows a mark-and-sweep approach:

1. Filter the operations.
2. Treat references from the remaining OpenAPI document as roots.
3. Recursively follow component dependencies through `$ref`.
4. Preserve referenced security schemes from OpenAPI Security Requirement Objects.
5. Remove all unreachable components.

This handles transitive dependencies such as:

```text
GET /users
  -> UserResponse
      -> User
          -> Address
              -> Country
```

If `UserResponse` is still used, the whole reachable dependency chain is preserved.

## In-place mode

By default the input dictionary is deep-copied. To mutate it directly:

```python
keep_openapi_operations(
    document,
    [("/users", "GET")],
    inplace=True,
)
```

The same `inplace=True` option is available for `remove_openapi_operations()`.

## Example

Run:

```bash
python example.py
```

The example keeps:

- only `GET /users`;
- all methods on `/health` via `("/health", "all")`.

After pruning:

- `User` remains because `GET /users` references it;
- `Address` remains because `User` references it;
- `CreateUserRequest` is removed because `POST /users` was removed;
- `AbsolutelyUnusedSchema` is removed because nothing references it.

## Notes

- Supported HTTP methods: `GET`, `PUT`, `POST`, `DELETE`, `OPTIONS`, `HEAD`, `PATCH`, `TRACE`.
- `all` is supported by `keep_openapi_operations()` only.
- Internal component references in the form `#/components/...` are followed.
- External references such as `other.yaml#/components/schemas/User` are intentionally not resolved or pruned.
- JSON Pointer escaping (`~0` and `~1`) is supported for component names.
- OpenAPI security schemes require special handling because Security Requirement Objects reference them by name rather than through `$ref`.
