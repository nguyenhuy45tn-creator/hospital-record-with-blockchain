# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2 and other packages
# Also install Node.js and npm for Ganache
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Ganache CLI globally
RUN npm install -g ganache

# Copy the project files into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8545 available for Ganache, 5000 for a Flask app and  5432 for PostgreSQL
EXPOSE 8545 5000 5432



# Define a default command to run when the container starts (optional)
# For example, to start Ganache and then a Flask app:
CMD ganache --database.dbPath chain --wallet.mnemonic "spatial draw combine river drive average bomb much riot brick prevent clog" --host 0.0.0.0 & python main.py
