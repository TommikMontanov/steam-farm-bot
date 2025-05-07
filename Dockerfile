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

RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -O packages-microsoft-prod.deb 
    && dpkg -i packages-microsoft-prod.deb 
    && rm packages-microsoft-prod.deb 
    && apt-get update && apt-get install -y dotnet-runtime-6.0 
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install aiogram aiohttp

# Download and extract ASF
RUN wget https://github.com/JustArchiNET/ArchiSteamFarm/releases/download/5.5.0.11/ASF-linux-x64.zip \
    && unzip ASF-linux-x64.zip -d ASF \
    && rm ASF-linux-x64.zip

RUN ls -la /app/ASF/

# Copy the bot and configuration files into the container
COPY main.py /app/
COPY ASF/config/ASF.json /app/ASF/config/ASF.json

# Set the proper permissions
RUN chmod +x /app/ASF/ArchiSteamFarm \
    && chmod -R 777 /app/ASF/config/

RUN echo "Checking port 1242 status..." && netstat -tuln | grep 1242 || echo "Port 1242 not open"

# Set the command to run the bot and ASF
CMD sh -c "dotnet /app/ASF/ArchiSteamFarm.dll & sleep 5 && netstat -tuln | grep 1242 && python3 /app/main.py"
