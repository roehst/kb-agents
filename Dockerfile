FROM python:3.12-slim

# Install SWI-Prolog and necessary dependencies
RUN apt-get update && apt-get install -y \
    swi-prolog \
    swi-prolog-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set SWI-Prolog environment variables
ENV SWI_HOME_DIR=/usr/lib/swi-prolog
ENV LIBSWIPL_PATH=/usr/lib/x86_64-linux-gnu/libswipl.so

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir pyswip python-dotenv openai

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default command
CMD ["python", "main.py"]