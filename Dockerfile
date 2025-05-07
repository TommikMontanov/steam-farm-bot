FROM python:3.9-slim

# Устанавливаем необходимые пакеты
RUN apt-get update && apt-get install -y \
    sqlite3 \
    unzip \
    wget \
    libicu-dev \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем .NET runtime
RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update && apt-get install -y dotnet-runtime-6.0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-библиотеки
RUN pip3 install aiogram aiohttp

# Устанавливаем рабочую директорию
WORKDIR /app

# Скачиваем и распаковываем ASF
RUN wget https://github.com/JustArchiNET/ArchiSteamFarm/releases/download/5.5.0.11/ASF-linux-x64.zip \
    && unzip ASF-linux-x64.zip -d ASF \
    && rm ASF-linux-x64.zip

# Проверяем содержимое директории ASF
RUN ls -la /app/ASF/ && test -f /app/ASF/ArchiSteamFarm.dll && echo "ArchiSteamFarm.dll exists" || { echo "ArchiSteamFarm.dll not found"; exit 1; }

# Копируем код бота
COPY main.py /app/

# Копируем конфигурацию ASF
COPY ASF/config/ASF.json /app/ASF/config/ASF.json

# Даем права на запись в директорию конфигурации
RUN chmod -R 777 /app/ASF/config/

# Проверяем, что порт 1242 открыт (для отладки)
RUN echo "Checking port 1242 status..." && netstat -tuln | grep 1242 || echo "Port 1242 not open"

# Запускаем ASF и бота
CMD sh -c "dotnet /app/ASF/ArchiSteamFarm.dll & sleep 15 && netstat -tuln | grep 1242 && python3 /app/main.py"
