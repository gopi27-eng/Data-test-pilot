# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app


# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

# Inform Docker that the app listens on port 8501
EXPOSE 8501

# This prevents Streamlit from crashing when it can't find a browser
ENV STREAMLIT_SERVER_HEADLESS=true


# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

