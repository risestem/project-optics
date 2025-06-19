FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    python3-dev \
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-recommended \
    texlive-luatex \
    dvipng \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Only copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
