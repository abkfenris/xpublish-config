"""Deeply merge configuration dictionaries."""


def merge(source, destination):
    """Merge source dict into destination dict recursively."""
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination
