# Use an official Python runtime as a base image
FROM python:3.12.4-slim

# Set environment variables to prevent Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container
COPY . /app/

# Copy the .env file into the container (make sure .env is in your .dockerignore)
# COPY .env /app/.env

# Collect static files for production
RUN python manage.py collectstatic --noinput

# Expose the port on which the app will run (default 8000)
EXPOSE 8000

# Install Daphne or Uvicorn (depending on the one you're using) for running ASGI
# Make sure you already added `channels` and `daphne`/`uvicorn` to requirements.txt
# If using Daphne:
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "ThreatDetection.asgi:application"]

# Alternatively, if using Uvicorn, replace the above CMD with:
# CMD ["gunicorn", "ThreatDetection.asgi:application", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
