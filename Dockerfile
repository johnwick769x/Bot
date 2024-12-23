# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose a port (optional, useful for debugging if needed)
EXPOSE 5000

# Command to run your bot
CMD ["python", "main.py"]
