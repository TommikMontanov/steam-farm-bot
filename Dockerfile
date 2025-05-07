FROM python:3.9-slim

# Устанавливаем необходимые пакеты
RUN apt-get update && apt-get install -y \
    sqlite3 \
    unzip \
    wget \
    libicu-dev \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем .NET 8.0 SDK (включает Microsoft.AspNetCore.App)
RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update && apt-get install -y dotnet-sdk-8.0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-библиотеки
RUN pip3 install aiogram aiohttp

# Создаем непривилегированного пользователя
RUN useradd -ms /bin/bash asfuser

# Устанавливаем рабочую директорию
WORKDIR /app
RUN chown asfuser:asfuser /app

# Скачиваем и распаковываем ASF (используем ASF-generic.zip)
RUN wget https://github.com/JustArchiNET/ArchiSteamFarm/releases/download/5.5.0.11/ASF-generic.zip \
    && unzip ASF-generic.zip -d ASF \
    && rm ASF-generic.zip \
    && chown -R asfuser:asfuser /app/ASF

# Проверяем содержимое директории ASF
RUN ls -la /app/ASF/ && test -f /app/ASF/ArchiSteamFarm.dll && echo "ArchiSteamFarm.dll exists" || { echo "ArchiSteamFarm.dll not found"; exit 1; }

# Копируем код бота
COPY main.py /app/
RUN chown asfuser:asfuser /app/main.py

# Копируем конфигурацию ASF
COPY ASF/config/ASF.json /app/ASF/config/ASF.json
RUN chown -R asfuser:asfuser /app/ASF/config/

# Даем права на запись в директорию конфигурации
RUN chmod -R 777 /app/ASF/config/

# Проверяем конфигурацию ASF
RUN cat /app/ASF/config/ASF.json

# Переключаемся на пользователя asfuser
USER asfuser

# Запуск ASF и ожидание его готовности перед запуском бота
CMD sh -c "dotnet /app/ASF/ArchiSteamFarm.dll & \
    until netstat -tuln | grep -q 1242; do \
        echo 'Waiting for ASF API...'; \
        sleep 5; \
    done; \
    echo 'ASF API is up!'; \
    python3 /app/main.py"
FROM python:3.9-slim

# Устанавливаем необходимые пакеты
RUN apt-get update && apt-get install -y \
    sqlite3 \
    unzip \
    wget \
    libicu-dev \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем .NET 8.0 SDK (включает Microsoft.AspNetCore.App)
RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update && apt-get install -y dotnet-sdk-8.0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-библиотеки
RUN pip3 install aiogram aiohttp

# Создаем непривилегированного пользователя
RUN useradd -ms /bin/bash asfuser

# Устанавливаем рабочую директорию
WORKDIR /app
RUN chown asfuser:asfuser /app

# Скачиваем и распаковываем ASF (используем ASF-generic.zip)
RUN wget https://github.com/JustArchiNET/ArchiSteamFarm/releases/download/5.5.0.11/ASF-generic.zip \
    && unzip ASF-generic.zip -d ASF \
    && rm ASF-generic.zip \
    && chown -R asfuser:asfuser /app/ASF

# Проверяем содержимое директории ASF
RUN ls -la /app/ASF/ && test -f /app/ASF/ArchiSteamFarm.dll && echo "ArchiSteamFarm.dll exists" || { echo "ArchiSteamFarm.dll not found"; exit 1; }

# Копируем код бота
COPY main.py /app/
RUN chown asfuser:asfuser /app/main.py

# Копируем конфигурацию ASF
COPY ASF/config/ASF.json /app/ASF/config/ASF.json
RUN chown -R asfuser:asfuser /app/ASF/config/

# Даем права на запись в директорию конфигурации
RUN chmod -R 777 /app/ASF/config/

# Проверяем конфигурацию ASF
RUN cat /app/ASF/config/ASF.json

# Переключаемся на пользователя asfuser
USER asfuser

# Запуск ASF и ожидание его готовности перед запуском бота
CMD sh -c "dotnet /app/ASF/ArchiSteamFarm.dll & \
    until netstat -tuln | grep -q 1242; do \
        echo 'Waiting for ASF API...'; \
        sleep 5; \
    done; \
    echo 'ASF API is up!'; \
    python3 /app/main.py"
