# youtube_simple.py
from clipysave import VideoDownloader
import os

# Создаем загрузчик с указанием текущей папки
downloader = VideoDownloader({
    'download_path': os.getcwd()  # Текущая папка
})

# URL видео
url = "https://youtu.be/QPQH6dP40YM?si=O0NL0eU80jco3aNR"

# Скачиваем видео
print("Скачиваю видео с YouTube в текущую папку...")
print(f"📁 Папка сохранения: {os.getcwd()}")
result = downloader.download(url)

# Проверяем результат
if result.success:
    print(f"\n✅ Видео скачано: {result.title}")
    print("📁 Файлы сохранены:")
    for file in result.files:
        if file.exists():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   📄 {file.name} ({size_mb:.1f} MB)")
else:
    print(f"\n❌ Ошибка: {result.error}")