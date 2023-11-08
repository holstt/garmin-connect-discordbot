FROM python:3.11.2-slim-buster AS runtime

WORKDIR /app

RUN pip install --upgrade pip

# Install poetry
RUN pip install poetry
RUN poetry --version

# Create layer with dependencies installed before copying the rest of the code.
COPY pyproject.toml poetry.lock /app/

# Do not create virtualenv when we are running in container ('poetry install' command will create a virtualenv if not disabled)
RUN poetry config virtualenvs.create false
# Install dependencies.
RUN poetry install --no-dev

# Copy only the files we need for running the app.
COPY ./main.py .
COPY ./src ./src

# Ensure non-root user, then run the app.
ENTRYPOINT \
  echo "Running as user: $(whoami) $(id -u):$(id -g)" && \
  if [ $(id -u) -eq 0 ] || [ $(id -G | grep -w 0) ]; then \
    echo 'Error: The container must not run as root or be part of root group.' \
    exit 1; \
  else \
    poetry run python main.py; \
  fi;

# Uncomment to keep the container running for debugging.
# ENTRYPOINT echo "Sleeping..." && sleep 99999

# Uncomment to allow running the container as root.
# ENTRYPOINT poetry run python main.py