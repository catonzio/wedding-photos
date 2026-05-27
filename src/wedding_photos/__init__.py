def main() -> None:
    import uvicorn

    uvicorn.run("wedding_photos.main:app", host="0.0.0.0", port=8000)
