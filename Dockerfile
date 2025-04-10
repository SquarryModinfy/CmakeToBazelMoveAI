FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
COPY main.py .
COPY gui.py .
# Config is optional now since we can use env vars
COPY config.yaml* ./ 2>/dev/null || :

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller

# Build with environment variable support
RUN pyinstaller --onefile --clean gui.py

# Document the configuration options in the image
LABEL description="CMake to Bazel migration tool. Configure using environment variables LLM_API_URL and LLM_API_KEY, or provide config.yaml"

# The built executable will be in /app/dist/gui