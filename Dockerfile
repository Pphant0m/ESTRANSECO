FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Unbuffer logs
ENV PYTHONUNBUFFERED=1

# Start the bot
CMD ["python", "ESTRANSECO.py"]