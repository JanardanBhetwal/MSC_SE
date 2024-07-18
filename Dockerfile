FROM python:3.11-slim


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire current directory to /app/
COPY . /app/

COPY start-server.sh /app/

# Ensure the start-server script is executable
RUN chmod +x /app/start-server.sh

# Verify the contents of the /app directory
RUN ls -l /app/

# Expose port 7188 for the application
EXPOSE 7188

# Run the application
ENTRYPOINT ["sh", "-c", "ls -l /app && /app/start-server.sh"]
