# vk_simple_local.py
from clipysave import VideoDownloader
import os

# Создаем загрузчик с указанием текущей папки
downloader = VideoDownloader({
    'download_path': os.getcwd()  # Текущая папка
})

url = "https://vkvideo.ru/video-111758246_456259268"

print("Скачиваю видео в текущую папку...")
result = downloader.download(url)

if result.success:
    print(f"✅ Видео скачано!")
    print(f"📌 Название: {result.title}")
    for file in result.files:
        print(f"📁 Файл: {file}")
        print(f"📊 Размер: {file.stat().st_size / 1024 / 1024:.1f} MB")
else:
    print(f"❌ Ошибка: {result.error}")