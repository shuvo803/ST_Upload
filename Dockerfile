FROM python:3.10

# Set the working directory in the container
WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Copy all the files from the current directory to /app in the container
COPY . /app/

# Install FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Render injects $PORT at runtime; bot.py reads it and binds the web server to it
EXPOSE 8000

# Command to run your Python script
CMD ["python3", "bot.py"]
