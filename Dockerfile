FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable stdout/stderr immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv and dependencies
RUN pip install --no-cache-dir pipenv

# Only copy Pipfiles first to leverage Docker layer caching
COPY Pipfile Pipfile.lock ./

# Install dependencies into the system environment
RUN PIPENV_VENV_IN_PROJECT=0 PIPENV_ALWAYS_YES=1 pipenv install --system --deploy

# Now copy the rest of the project
COPY . .

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh || true

EXPOSE 8000

# Default command can be overridden by docker-compose
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


