# Base image for Python
FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y postgresql-client

# Set the working directory
WORKDIR /app

# Copy all files to the working directory
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Command to run FastAPI with Uvicorn
CMD ["uvicorn", "sbs.main:app", "--host", "0.0.0.0", "--port", "8000"]
