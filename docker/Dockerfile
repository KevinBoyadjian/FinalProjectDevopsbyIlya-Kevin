# --- STAGE 1: Builder ---
FROM python:3.12-alpine AS builder

# Set the working directory
WORKDIR /app

# Install temporary build dependencies (needed for some Python libraries)
RUN apk add --no-cache gcc musl-dev linux-headers

# Copy the requirements file
COPY requirements.txt .

# Install dependencies to a temporary folder
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 2. THE FORCE PATCH: Overwrite any transitive downgrades into the same folder
RUN pip install --no-cache-dir --upgrade --prefix=/install "urllib3>=2.7.0"



# --- STAGE 2: Final Runtime ---
FROM python:3.12-alpine

# Set the working directory
WORKDIR /app 

# Copy only the installed Python packages from the builder stage
# This keeps the image small and secure
COPY --from=builder /install /usr/local

# Copy the application folder
COPY app/ .

# DevSecOps best practice: Create and use a non-root user
# We dont want to run our app as 'root' for security reasons
RUN adduser -D football_user && \
    chown -R football_user:football_user /app

# Switch to the new user
USER football_user

# Set invironment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Flask usually runs on 5000
EXPOSE 5000

# Run the app using Gunicorn
# "app:app" means: (folder app) : (variable app)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
