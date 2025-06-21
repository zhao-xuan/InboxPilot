FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY webhook_monitor/requirements.txt ./webhook_monitor/
COPY mcp_server/requirements.txt ./mcp_server/

# Install Python dependencies
RUN pip install --no-cache-dir -r webhook_monitor/requirements.txt
RUN pip install --no-cache-dir -r mcp_server/requirements.txt

# Copy application code
COPY . .

# Install MCP server
RUN cd mcp_server && pip install -e .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the webhook monitor
CMD ["python", "webhook_monitor/email_monitor.py"] 