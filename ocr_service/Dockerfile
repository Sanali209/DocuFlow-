FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# libgl1-mesa-glx and libglib2.0-0 are often required for image processing libraries (like cv2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models if possible (optional, but good for startup time)
# RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

COPY . .

# Create a non-root user (Standard for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
