# instagram_simple.py
from clipysave import VideoDownloader
import os

# Создаем загрузчик с указанием текущей папки
downloader = VideoDownloader({
    'download_path': os.getcwd()  # Текущая папка
})

# URL Instagram поста или рилса
url = "https://www.instagram.com/reel/DU518DCCFvH/?igsh=MWJmeGI4ZmJlMXgweg=="

print("Скачиваю с Instagram в текущую папку...")
print(f"📁 Папка сохранения: {os.getcwd()}")
result = downloader.download(url)

if result.success:
    print(f"\n✅ Instagram контент скачан!")
    print("📁 Файлы сохранены:")
    for file in result.files:
        if file.exists():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   📄 {file.name} ({size_mb:.1f} MB)")
else:
    print(f"❌ Ошибка: {result.error}")