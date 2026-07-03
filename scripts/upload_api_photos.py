import asyncio
import mimetypes
import re
from pathlib import Path
from httpx import AsyncClient


def get_endpoint(table_id: int, local: bool = True) -> str:
    if local:
        return f"http://192.168.68.64:8000/wedding-photos/api/admin/tables/{table_id}/photos"
    else:
        return f"https://danilocatone.com/wedding-photos/api/admin/tables/{table_id}/photos"


TOKEN = "vzHqQQ"
TABLE_NAME_PATTERN = re.compile(r"^Capitolo\s+(\d+)\b")
PHOTOS_FOLDER = Path("/Users/dcatone/Desktop/Foto_Tavoli_sito/Foto tableau")


def extract_table_id(table_name: str) -> int | None:
    match = TABLE_NAME_PATTERN.match(table_name)
    if not match:
        return None
    return int(match.group(1))


async def upload_single_photo(
    client: AsyncClient,
    endpoint: str,
    photo: Path,
) -> bool:
    content_type, _ = mimetypes.guess_type(photo.name)

    try:
        with photo.open("rb") as file_handle:
            response = await client.post(
                endpoint,
                files=[
                    (
                        "files",
                        (
                            photo.name,
                            file_handle,
                            content_type or "application/octet-stream",
                        ),
                    )
                ],
            )
    except Exception as exc:
        print(f"  [{photo.name}] failed with exception: {exc}")
        return False

    if response.is_success:
        print(f"  [{photo.name}] uploaded: HTTP {response.status_code}")
        return True

    print(f"  [{photo.name}] failed: HTTP {response.status_code}")
    print(f"  Response: {response.text}")
    return False


async def upload_table_photos(client: AsyncClient, table: Path) -> None:
    table_name = table.name
    table_id = extract_table_id(table_name)
    if table_id is None:
        print(f"Skipping table with unrecognized name format: {table_name}")
        return

    photos = sorted(photo for photo in table.glob("*") if photo.is_file())
    if not photos:
        print(f"Skipping table {table_name}: no photos found")
        return

    endpoint = get_endpoint(table_id=table_id, local=True)
    print(
        f"Uploading {len(photos)} photos for table {table_id} ({table_name}) in parallel"
    )

    tasks = [upload_single_photo(client, endpoint, photo) for photo in photos]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = 0
    failure_count = 0
    for result in results:
        if isinstance(result, Exception):
            failure_count += 1
            print(f"  Upload task failed with exception: {result}")
            continue

        if result:
            success_count += 1
        else:
            failure_count += 1

    print(
        f"Table {table_id} completed: {success_count} uploaded, {failure_count} failed"
    )
    print()


async def main() -> None:
    photos_folder = Path(PHOTOS_FOLDER)
    tables = sorted(table for table in photos_folder.glob("*") if table.is_dir())

    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with AsyncClient(headers=headers, timeout=120.0) as client:
        for table in tables:
            await upload_table_photos(client, table)


if __name__ == "__main__":
    asyncio.run(main())
