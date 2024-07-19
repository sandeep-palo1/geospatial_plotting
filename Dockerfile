FROM geospatial-env-base:latest

RUN git clone https://github.com/sandeep-palo1/INDIA_PINCODES.git

WORKDIR /app/INDIA_PINCODES

RUN bash organiser.sh

WORKDIR /app

COPY ./admin_boundaries_database/ ./admin_boundaries_database

COPY ./geographical_division_handlers ./geographical_division_handlers

# Copy the entrypoint script into the container
COPY entrypoint.sh /app/entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Define the entry point
ENTRYPOINT ["/app/entrypoint.sh"]
