FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ src/
COPY docs/ docs/
COPY AGENTS.md .
COPY README.md .

# Expose port
EXPOSE 8080

# Environment variables
ENV DOCUFLOW_NODE_ID=NODE_1
ENV DOCUFLOW_SHARED_PATH=/shared

# Default command
CMD ["uv", "run", "python", "-m", "docuflow.main"]