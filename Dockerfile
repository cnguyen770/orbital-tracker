# Use an official Python runtime as a parent image.
# "slim" is a stripped-down Debian image — smaller download, faster startup.
FROM python:3.12-slim

# Set the working directory inside the container.
# All subsequent commands run from here.
WORKDIR /app

# Prevent Python from buffering stdout/stderr — important for seeing logs in real time
ENV PYTHONUNBUFFERED=1

# Install OS-level dependencies.
# psycopg2 needs libpq-dev to compile; gcc is the C compiler it uses.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy just requirements first, separate from the rest of the code.
# This is a Docker caching optimization — as long as requirements.txt
# doesn't change, Docker reuses the cached layer with all pip installs
# instead of reinstalling every rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code.
# Code changes much more often than dependencies, so this layer rebuilds
# on every change — but it's fast because it's just copying files.
COPY . .

# Document that this container listens on port 8000.
# This is metadata — doesn't actually open the port, just tells users/tools.
EXPOSE 8000

# Default command when the container starts.
# We'll override this in docker-compose for development.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]