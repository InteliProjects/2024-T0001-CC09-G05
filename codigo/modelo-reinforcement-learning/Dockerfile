# Use the official PyTorch image with CUDA support
FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy all files in the current directory to the working directory in the container
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r ./requirements.txt

# Command to run the Streamlit application on port 8501 by default
CMD ["streamlit", "run", "main.py", "--server.address", "0.0.0.0", "--server.port", "8501"]