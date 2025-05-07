# Use an official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Update package list and install necessary packages
RUN apt-get update && apt-get install -y \
    sqlite3 \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install aiogram aiohttp

# Download and extract ASF
RUN wget https://github.com/JustArchiNET/ArchiSteamFarm/releases/download/5.5.0.11/ASF-generic.zip \
    && unzip ASF-generic.zip -d ASF \
    && rm ASF-generic.zip

# Copy the bot and configuration files into the container
COPY main.py /app/
COPY ASF.json ASF/config/ASF.json

# Set the proper permissions
RUN chmod +x /app/ASF/ArchiSteamFarm \
    && chmod -R 777 /app/ASF/config/

# Set the command to run the bot and ASF
CMD /app/ASF/ArchiSteamFarm & python3 /app/main.py
