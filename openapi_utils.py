from __future__ import annotations

import copy
from collections import defaultdict, deque
from typing import Any, Iterable


HTTP_METHODS = {
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
}

ALL_METHODS = "all"


def remove_openapi_operations(
    document: dict[str, Any],
    operations_to_remove: Iterable[tuple[str, str]],
    *,
    remove_empty_paths: bool = True,
    inplace: bool = False,
) -> dict[str, Any]:
    """
    Remove selected OpenAPI operations and then prune components that are no
    longer reachable from the remaining document.

    Args:
        document: OpenAPI document already loaded into a Python dict.
        operations_to_remove: Iterable of (path, method) tuples.
        remove_empty_paths: Remove a path item if it becomes completely empty.
        inplace: Mutate the input document instead of deep-copying it.

    Returns:
        The pruned OpenAPI document.
    """

    if not inplace:
        document = copy.deepcopy(document)

    _remove_operations(
        document,
        operations_to_remove,
        remove_empty_paths=remove_empty_paths,
    )
    _remove_unused_components(document)

    return document


def keep_openapi_operations(
    document: dict[str, Any],
    operations_to_keep: Iterable[tuple[str, str]],
    *,
    inplace: bool = False,
) -> dict[str, Any]:
    """
    Keep only selected OpenAPI operations and prune components that are no
    longer reachable from the resulting document.

    Use method ``"all"`` to keep every HTTP operation that exists for a path.

    Examples:
        [("/users", "GET"), ("/orders/{id}", "DELETE")]
        [("/users", "all")]

    Path-level metadata such as ``parameters``, ``summary``, ``description``,
    ``servers`` and ``$ref`` is preserved for paths that remain.

    Args:
        document: OpenAPI document already loaded into a Python dict.
        operations_to_keep: Iterable of (path, method) tuples. ``method`` may
            be a normal HTTP method or ``"all"``.
        inplace: Mutate the input document instead of deep-copying it.

    Returns:
        The filtered and pruned OpenAPI document.
    """

    if not inplace:
        document = copy.deepcopy(document)

    _keep_operations(document, operations_to_keep)
    _remove_unused_components(document)

    return document


def _remove_operations(
    document: dict[str, Any],
    operations_to_remove: Iterable[tuple[str, str]],
    *,
    remove_empty_paths: bool,
) -> None:
    paths = document.get("paths")

    if not isinstance(paths, dict):
        return

    for path, method in operations_to_remove:
        method = _normalize_http_method(method, allow_all=False)

        path_item = paths.get(path)
        if not isinstance(path_item, dict):
            continue

        path_item.pop(method, None)

        if remove_empty_paths and not path_item:
            paths.pop(path, None)


def _keep_operations(
    document: dict[str, Any],
    operations_to_keep: Iterable[tuple[str, str]],
) -> None:
    paths = document.get("paths")

    if not isinstance(paths, dict):
        return

    methods_by_path: dict[str, set[str]] = defaultdict(set)

    for path, method in operations_to_keep:
        normalized_method = _normalize_http_method(method, allow_all=True)
        methods_by_path[path].add(normalized_method)

    for path in list(paths):
        path_item = paths[path]

        if path not in methods_by_path:
            del paths[path]
            continue

        if not isinstance(path_item, dict):
            continue

        methods_to_keep = methods_by_path[path]

        if ALL_METHODS in methods_to_keep:
            continue

        for key in list(path_item):
            normalized_key = key.lower() if isinstance(key, str) else key

            if normalized_key in HTTP_METHODS and normalized_key not in methods_to_keep:
                del path_item[key]


def _normalize_http_method(method: str, *, allow_all: bool) -> str:
    if not isinstance(method, str):
        raise TypeError(f"HTTP method must be a string, got {type(method).__name__}")

    normalized = method.lower()
    allowed_methods = HTTP_METHODS | ({ALL_METHODS} if allow_all else set())

    if normalized not in allowed_methods:
        raise ValueError(
            f"Unsupported HTTP method: {method!r}. "
            f"Expected one of: {sorted(allowed_methods)}"
        )

    return normalized


def _remove_unused_components(document: dict[str, Any]) -> None:
    """Prune unreachable entries from OpenAPI components using mark-and-sweep."""

    components = document.get("components")
    if not isinstance(components, dict):
        return

    component_index: dict[tuple[str, str], Any] = {}

    for component_type, items in components.items():
        if not isinstance(items, dict):
            continue

        for component_name, component_value in items.items():
            component_index[(component_type, component_name)] = component_value

    document_without_components = {
        key: value
        for key, value in document.items()
        if key != "components"
    }

    reachable: set[tuple[str, str]] = set()
    queue: deque[tuple[str, str]] = deque()

    def mark(component: tuple[str, str]) -> None:
        if component not in component_index or component in reachable:
            return

        reachable.add(component)
        queue.append(component)

    for ref in _find_refs(document_without_components):
        component = _parse_component_ref(ref)
        if component is not None:
            mark(component)

    for security_scheme in _find_security_scheme_references(
        document_without_components
    ):
        mark(("securitySchemes", security_scheme))

    while queue:
        component_key = queue.popleft()
        component_value = component_index[component_key]

        for ref in _find_refs(component_value):
            referenced_component = _parse_component_ref(ref)
            if referenced_component is not None:
                mark(referenced_component)

        for security_scheme in _find_security_scheme_references(component_value):
            mark(("securitySchemes", security_scheme))

    for component_type, items in list(components.items()):
        if not isinstance(items, dict):
            continue

        for component_name in list(items):
            if (component_type, component_name) not in reachable:
                del items[component_name]

        if not items:
            del components[component_type]

    if not components:
        document.pop("components", None)


def _find_refs(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        ref = value.get("$ref")

        if isinstance(ref, str):
            yield ref

        for child in value.values():
            yield from _find_refs(child)

    elif isinstance(value, list):
        for child in value:
            yield from _find_refs(child)


def _parse_component_ref(ref: str) -> tuple[str, str] | None:
    """
    Convert an internal component ref such as
    '#/components/schemas/User' into ('schemas', 'User').

    External refs are intentionally ignored.
    """

    prefix = "#/components/"
    if not ref.startswith(prefix):
        return None

    pointer = ref[len(prefix):]
    parts = pointer.split("/")

    if len(parts) < 2:
        return None

    component_type = _decode_json_pointer(parts[0])
    component_name = _decode_json_pointer(parts[1])

    return component_type, component_name


def _decode_json_pointer(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _find_security_scheme_references(value: Any) -> Iterable[str]:
    """Find security scheme names referenced by Security Requirement Objects."""

    if isinstance(value, dict):
        for key, child in value.items():
            if key == "security" and isinstance(child, list):
                for security_requirement in child:
                    if not isinstance(security_requirement, dict):
                        continue

                    for scheme_name in security_requirement:
                        if isinstance(scheme_name, str):
                            yield scheme_name

            yield from _find_security_scheme_references(child)

    elif isinstance(value, list):
        for child in value:
            yield from _find_security_scheme_references(child)
