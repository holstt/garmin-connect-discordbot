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

# Print user at startup to verify we are running as expected user (e.g. not root)
ENTRYPOINT echo "Running as user: $(whoami) $(id -u):$(id -g)" && poetry run python main.py