FROM python:3.11-slim

# Install FFmpeg (and clean up apt caches)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set /code as your base working directory
WORKDIR /code

# Copy and install dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the application code into the container
COPY app /code/app

# Change the working directory to app
WORKDIR /code/app

# Finally, run your main.py
CMD ["python3", "main_page.py"]