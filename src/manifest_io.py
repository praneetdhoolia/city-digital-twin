"""Read complete provenance fields in manifests of any city size."""
import csv
import os
from contextlib import contextmanager
from pathlib import Path
import tempfile


@contextmanager
def atomic_manifest_writer(path, *, newline):
    """Publish one complete manifest file, retaining its predecessor on failure.

    The temporary file shares the destination's filesystem. JSON and CSV are
    each complete snapshots; this does not make their two replacements a single
    transaction or freeze the underlying data while a build is in progress.
    """
    target = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline=newline,
                                         dir=target.parent, prefix='.' + target.name + '.',
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def manifest_reader(stream):
    """Return a CSV reader sized to the actual manifest, without truncation.

    A field cannot contain more characters than the file has encoded bytes.
    The CSV decoder's limit is process-wide: only raise it so nested readers
    cannot invalidate an already-open larger manifest.
    """
    csv.field_size_limit(max(csv.field_size_limit(), os.fstat(stream.fileno()).st_size))
    return csv.DictReader(stream)
