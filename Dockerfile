FROM python:3.14-slim

# Copy source code and install dependencies
COPY pyproject.toml README.md uv.lock /app/
COPY src/ /app/src/
WORKDIR /app

# Install uv and sync dependencies
RUN pip install --no-cache-dir uv
RUN uv sync --frozen --no-dev

# Copy required files
COPY static /app/static
COPY tables.yaml /app/tables.yaml

EXPOSE 8000
CMD [".venv/bin/python", "-m", "fastapi", "run", "src/wedding_photos/main.py", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["sleep", "inf"]