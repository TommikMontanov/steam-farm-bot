RUN apt-get update && apt-get install -y python3 python3-pip
sqlite3 
unzip 
wget 
&& rm -rf /var/lib/apt/lists/*
pip3 install aiogram aiohttp
workdir /app
run wget https://github.com/JustArchiNET/ArchiSteamFarm/releases/download/5.5.0.11/ASF-generic.zip 
&& unzip ASF-generic.zip -d ASF 
&& rm ASF-generic.zip
copy telegram_bot.py /app/
copy ASF.json /app/ASF/config/
run chmod +x /app/ASF/ArchiSteamFarm 
&& chmod -R 777 /app/ASF/config/
cmd /app/ASF/ArchiSteamFarm & python3 /app/telegram_bot.py
