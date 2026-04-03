# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (this leverages Docker cache to speed up future builds)
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY main.py .
COPY .streamlit/ .streamlit/

# Expose the port Streamlit uses by default
EXPOSE 8501

# Add healthcheck to ensure the container is running correctly (optional but recommended)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Command to start the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]