FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY agents ./agents
COPY data/samples ./data/samples

RUN pip install --no-cache-dir ".[live]"

# Reports land in /reports; mount it to keep them.
# Pass -e ANTHROPIC_API_KEY=... and add --live for Claude-powered judgment steps.
ENTRYPOINT ["python", "-m", "revops"]
CMD ["run", "--out", "/reports"]
