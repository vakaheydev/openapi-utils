# OpenAPI Utils

Small Python utilities for transforming OpenAPI documents.

## Remove operations and prune unused components

`remove_openapi_operations()` removes selected operations from an OpenAPI document and then removes components that are no longer reachable from the remaining document.

The important part is that shared components are preserved.

For example, if both `GET /users` and `POST /users` reference `#/components/schemas/User`, removing only `POST /users` will **not** remove `User`, because `GET /users` still uses it.

The pruning algorithm follows a mark-and-sweep approach:

1. Remove the selected operations.
2. Treat references from the remaining OpenAPI document as roots.
3. Recursively follow component dependencies through `$ref`.
4. Preserve referenced security schemes from OpenAPI Security Requirement Objects.
5. Remove all unreachable components.

This also handles transitive dependencies such as:

```text
GET /users
  -> UserResponse
      -> User
          -> Address
              -> Country
```

If `UserResponse` is still used, the whole reachable dependency chain is preserved.

## Usage

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

By default the input dictionary is deep-copied. To mutate it directly:

```python
remove_openapi_operations(
    document,
    [("/users", "POST")],
    inplace=True,
)
```

## Example

Run:

```bash
python example.py
```

The example removes `POST /users`.

After pruning:

- `User` remains because `GET /users` still references it.
- `Address` remains because `User` references it.
- `CreateUserRequest` is removed because it was only used by `POST /users`.
- `AbsolutelyUnusedSchema` is removed because nothing references it.

## Notes

- Internal component references in the form `#/components/...` are followed.
- External references such as `other.yaml#/components/schemas/User` are intentionally not resolved or pruned.
- JSON Pointer escaping (`~0` and `~1`) is supported for component names.
- OpenAPI security schemes require special handling because Security Requirement Objects reference them by name rather than through `$ref`.
