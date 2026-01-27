FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# libgl1 and libglib2.0-0 are often required for image processing libraries (like cv2)
# libgl1-mesa-glx is deprecated/unavailable in newer Debian versions
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user (Standard for Hugging Face Spaces)
RUN useradd -m -u 1000 user

# Set environment variables to ensure models are downloaded to a writable directory
# Docling/RapidOCR and HuggingFace Hub use these
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    RAPIDOCR_CACHE_DIR=/home/user/.cache/rapidocr \
    XDG_CACHE_HOME=/home/user/.cache

# Create cache directories and set permissions
RUN mkdir -p /home/user/.cache/huggingface \
    /home/user/.cache/rapidocr \
    && chown -R user:user /home/user

# Switch to user to run the pre-download script
# This ensures files are owned by 'user' and not 'root'
USER user

# Pre-download models by initializing the converter once
# This will trigger downloads into the writable cache directories defined above
RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

COPY --chown=user:user . .

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
