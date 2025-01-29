# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY telegram_bot.py .
COPY config.json .

# Create a directory for downloads
RUN mkdir -p /app/Video

# Expose any necessary ports (if your bot uses a webhook, expose the port)
EXPOSE 8443

# Run the bot script when the container launches
CMD ["python", "telegram_bot.py"]