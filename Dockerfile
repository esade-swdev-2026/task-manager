FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY README.md LICENSE ./
COPY src ./src
RUN uv sync --locked --no-dev

RUN useradd --create-home app && mkdir /app/storage_tasks && chown app:app /app/storage_tasks
USER app

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["task-manager"]
CMD ["--help"]