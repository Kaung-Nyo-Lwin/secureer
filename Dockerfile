# Use the official Python image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Create a writable directory for SQLite database
RUN mkdir -p /app/db && chmod -R 777 /app/db

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Expose the port for the application
EXPOSE 8000

# Run migrations and start the Django development server

RUN python manage.py migrate --noinput

#RUN python manage.py collectstatic --noinput

#CMD ["python", "manage.py", "migrate"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
