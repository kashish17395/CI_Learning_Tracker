"""Report (default) or delete orphaned certificate objects older than 24 hours."""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import select
from app.core.security import utc
from app.db.session import SessionLocal
from app.models import Certificate
from app.storage.service import LocalStorage, S3Storage, storage


def objects(store):
    if isinstance(store, S3Storage):
        paginator = store.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=store.bucket, Prefix="certificates/"):
            for item in page.get("Contents", []):
                yield item["Key"], item["LastModified"]
    elif isinstance(store, LocalStorage):
        root = store.root / "certificates"
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    yield path.relative_to(
                        store.root
                    ).as_posix(), datetime.fromtimestamp(
                        path.stat().st_mtime, timezone.utc
                    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete confirmed old orphan objects; default is read-only",
    )
    args = parser.parse_args()
    store = storage()
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    with SessionLocal() as db:
        known = set(db.scalars(select(Certificate.blob_key)))
        for key, modified in objects(store):
            if key not in known and utc(modified) < cutoff:
                print(("DELETE " if args.delete else "ORPHAN ") + key)
                if args.delete:
                    # Recheck immediately before deletion. The 24-hour grace period
                    # protects in-flight uploads that have not committed metadata.
                    if not db.scalar(
                        select(Certificate.id).where(Certificate.blob_key == key)
                    ):
                        store.delete(key)


if __name__ == "__main__":
    main()
