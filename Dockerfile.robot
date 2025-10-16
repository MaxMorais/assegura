# Robot Framework Test Execution Environment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies for Robot Framework and browser automation
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Install Robot Framework and dependencies
RUN pip install \
    robotframework==6.1.1 \
    robotframework-requests==0.9.4 \
    robotframework-databaselibrary==1.2.4 \
    robotframework-seleniumlibrary==6.2.0 \
    selenium==4.15.2 \
    webdriver-manager==4.0.1

# Install Chrome for Selenium tests
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /tests /results /contract_tests

# Set working directory
WORKDIR /tests

# Create non-root user
RUN groupadd -r robot && useradd -r -g robot robot
RUN chown -R robot:robot /tests /results /contract_tests

# Switch to non-root user
USER robot

# Default command
CMD ["robot", "--outputdir", "/results", "/tests"]