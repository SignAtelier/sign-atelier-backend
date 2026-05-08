import io
from collections.abc import Iterator
from datetime import datetime
from typing import Protocol


class ObjectStorage(Protocol):
    async def upload(self, buffer: io.BytesIO, file_name: str) -> None:
        """Upload a file-like object to object storage."""

    async def generate_read_url(self, file_name: str) -> str:
        """Create a temporary URL for reading an object."""

    async def delete(self, file_name: str) -> None:
        """Delete an object from storage."""

    async def copy_and_delete(self, source: str, destination: str) -> None:
        """Copy an object to a new key, then remove the original."""

    async def get_stream(self, file_name: str) -> tuple[Iterator[bytes], str]:
        """Return an object byte iterator and content type."""

    async def list_keys(
        self, prefix: str
    ) -> list[tuple[str, datetime | None]]:
        """Return object keys and their last-modified timestamps."""
