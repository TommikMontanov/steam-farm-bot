from mcr.microsoft.com/dotnet/runtime:8.0
RUN apt-get update && apt-get install -y 
python3 
python3-pip 
sqlite3 
unzip 
wget 
&& rm -rf /var/lib/apt/lists/*
RUN pip3 install aiogram aiohttp
WORKDIR /app RUN wget https://github.com/JustArchiNET/ArchiSteamFarm/releases/latest/download/ASF-generic.zip 
&& unzip ASF-generic.zip -d ASF 
&& rm ASF-generic.zip
COPY telegram_bot.py /app/
COPY ASF.json /app/ASF/config/ COPY Bot.json /app/ASF/config/
RUN chmod +x /app/ASF/ArchiSteamFarm
CMD /app/ASF/ArchiSteamFarm & python3 /app/telegram_bot.py
