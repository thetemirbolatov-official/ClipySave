#!/usr/bin/env python3
"""
VK Video/Music Downloader
Автор: @thetemirbolatov
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Для Windows кодировки
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def set_console_icon():
    """Устанавливает иконку для консоли (для Windows)"""
    if sys.platform == 'win32':
        try:
            icon_path = Path('datas/logo.ico')
            if icon_path.exists():
                # Меняем заголовок окна
                os.system(f'title VK/YouTube Downloader by @thetemirbolatov')
                
                # Для иконки в панели задач используем ctypes
                import ctypes
                # Получаем handle консоли
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                user32 = ctypes.WinDLL('user32', use_last_error=True)
                
                # Находим окно консоли
                console_handle = kernel32.GetConsoleWindow()
                if console_handle:
                    # Загружаем иконку из файла
                    large_icon = ctypes.wintypes.HICON(
                        user32.LoadImageW(
                            0, str(icon_path.absolute()), 1,  # 1 = IMAGE_ICON
                            32, 32, 0x00000010  # LR_LOADFROMFILE
                        )
                    )
                    small_icon = ctypes.wintypes.HICON(
                        user32.LoadImageW(
                            0, str(icon_path.absolute()), 1,
                            16, 16, 0x00000010
                        )
                    )
                    
                    # Устанавливаем иконки
                    user32.SendMessageW(console_handle, 0x0080, 0, small_icon)  # WM_SETICON - small
                    user32.SendMessageW(console_handle, 0x0080, 1, large_icon)  # WM_SETICON - large
                    
        except Exception as e:
            pass  # Игнорируем ошибки с иконкой

def show_logo():
    """Показывает логотип приложения"""
    # Устанавливаем иконку
    set_console_icon()
    
    # Текстовый логотип
    print('╔════════════════════════════════╗')
    print('║     VK/YouTube Downloader      ║')
    print('║     by @thetemirbolatov        ║')
    print('╚════════════════════════════════╝')
    
    # Проверяем наличие иконки
    icon_path = Path('datas/logo.ico')
    if icon_path.exists():
        print(f'📁 Иконка загружена: {icon_path}')
    else:
        print('📁 Создайте папку datas и добавьте logo.ico')
        
def download_instagram(url):
    """Скачивает с Instagram через instaloader"""
    print("\n[Instagram Downloader]")
    print("Начинаю загрузку...\n")
    
    try:
        # Пробуем импортировать instaloader
        try:
            import instaloader
            from instaloader import Post
        except ImportError:
            print("❌ instaloader не установлен")
            print("Установите: pip install instaloader")
            return False
        
        # Создаем экземпляр Instaloader без сохранения лишних файлов
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,  # Не сохранять JSON
            compress_json=False,
            post_metadata_txt_pattern='',  # Не создавать txt файлы
            max_connection_attempts=3,
            request_timeout=30.0,
            quiet=True  # Меньше вывода
        )
        
        # Извлекаем короткий код из URL
        import re
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
            r'instagram\.com/tv/([^/?]+)'
        ]
        
        shortcode = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                shortcode = match.group(1)
                # Очищаем от лишних параметров
                shortcode = shortcode.split('?')[0]
                break
        
        if not shortcode:
            print("❌ Неверная ссылка Instagram")
            return False
        
        print(f"🔗 Shortcode: {shortcode}")
        
        # Получаем пост по короткому коду
        try:
            post = Post.from_shortcode(L.context, shortcode)
            
            # Информация о посте
            if post.is_video:
                print(f"🎬 Видео | Длительность: {post.video_duration:.1f} сек")
            else:
                print(f"📸 Фото" + (f" ({post.mediacount} шт)" if post.mediacount > 1 else ""))
            
            if post.caption:
                caption = post.caption[:100] + "..." if len(post.caption) > 100 else post.caption
                print(f"📝 {caption}")
            
            print(f"❤️ {post.likes} лайков")
            if post.is_video and post.video_view_count:
                print(f"👁️ {post.video_view_count} просмотров")
            
            print("\n⏳ Скачивание...")
            
            # Скачиваем пост
            L.download_post(post, target='.')
            
            # Ищем скачанные файлы (видео или фото)
            downloaded = False
            current_dir = Path('.')
            
            # Ищем видео файлы
            video_files = list(current_dir.glob(f'*{shortcode}*.mp4')) + \
                         list(current_dir.glob(f'*{shortcode}*.mov'))
            
            # Ищем фото файлы
            photo_files = list(current_dir.glob(f'*{shortcode}*.jpg')) + \
                         list(current_dir.glob(f'*{shortcode}*.png'))
            
            # Удаляем JSON и txt файлы если они создались
            for json_file in current_dir.glob(f'*{shortcode}*.json'):
                json_file.unlink()
            for txt_file in current_dir.glob(f'*{shortcode}*.txt'):
                txt_file.unlink()
            
            # Показываем что скачалось
            if video_files:
                print(f"\n✅ Скачано видео:")
                for f in video_files:
                    size = f.stat().st_size / (1024*1024)
                    print(f"   📁 {f.name} ({size:.1f} MB)")
                downloaded = True
            
            if photo_files:
                print(f"\n✅ Скачано фото:")
                for f in photo_files:
                    size = f.stat().st_size / (1024*1024)
                    print(f"   📁 {f.name} ({size:.1f} MB)")
                downloaded = True
            
            if not downloaded:
                print("\n⚠️ Файлы не найдены, но возможно скачались:")
                all_files = list(current_dir.glob(f'*{shortcode}*'))
                for f in all_files:
                    size = f.stat().st_size / (1024*1024)
                    print(f"   📁 {f.name} ({size:.1f} MB)")
                    downloaded = True
            
            print("\n✅ Загрузка завершена!")
            return True
            
        except instaloader.exceptions.ProfileNotExistsException:
            print("❌ Профиль не существует")
            return False
        except instaloader.exceptions.PrivateProfileException:
            print("🔒 Приватный профиль. Нужна авторизация")
            return False
        except instaloader.exceptions.LoginRequiredException:
            print("🔒 Требуется авторизация")
            return False
        except Exception as e:
            print(f"❌ Ошибка при получении поста: {e}")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False

def download_media(url):
    """Скачивает видео или музыку с VK или YouTube"""
    
    # Определяем источник
    if 'youtube.com' in url or 'youtu.be' in url or 'm.youtube.com' in url:
        source = 'YouTube'
    elif 'instagram.com' in url:
        return download_instagram(url)
    else:
        source = 'VK'
    
    print(f"\n[{source} Downloader]")
    print("Начинаю загрузку...\n")
    
    # Базовая команда
    cmd = [
        'yt-dlp',
        '--progress',
        '--newline',
        '--no-part',
        '--restrict-filenames',
        '--output', '%(title)s.%(ext)s',
        '--socket-timeout', '30',
        '--retries', '5',
        '--fragment-retries', '5',
    ]
    
    # Настройки для разных источников
    if source == 'VK':
        cmd.extend([
            '--format', 'best[height<=1080]',
            '--user-agent', 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36',
            '--referer', 'https://vk.com/',
        ])
        # Добавляем cookies для VK если есть
        cookie_file = Path('cookie.txt')
        if cookie_file.exists() and cookie_file.stat().st_size > 0:
            cmd.extend(['--cookies', 'cookie.txt'])
    else:
        # Для YouTube лучшее качество
        cmd.extend([
            '--format', 'bestvideo+bestaudio/best',
            '--merge-output-format', 'mp4',
            '--embed-thumbnail',
            '--embed-metadata',
        ])
    
    cmd.append(url)
    
    try:
        # Запускаем процесс
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        
        # Отслеживаем прогресс
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
            # Показываем только прогресс и важные сообщения
            if '[download]' in line:
                if '%' in line:
                    # Парсим процент
                    try:
                        parts = line.split()
                        for part in parts:
                            if '%' in part and part.replace('%', '').replace('.', '').isdigit():
                                percent = part
                                # Создаем прогресс бар
                                p = float(percent.replace('%', ''))
                                bar_len = 30
                                filled = int(bar_len * p / 100)
                                bar = '█' * filled + '░' * (bar_len - filled)
                                print(f'\r[{bar}] {percent} {parts[-1] if len(parts) > 1 else ""}', end='', flush=True)
                                break
                    except:
                        print(f'\r{line}', end='', flush=True)
                elif 'Destination' in line:
                    print(f'\n{line}')
                elif 'has already been downloaded' in line:
                    print(f'\n✅ Файл уже скачан')
            elif 'ERROR:' in line:
                if 'Video unavailable' in line:
                    print(f'\n❌ Видео недоступно')
                elif 'Private video' in line:
                    print(f'\n🔒 Видео приватное')
                else:
                    print(f'\n❌ {line}')
            elif 'WARNING:' in line:
                if 'requested format not available' in line:
                    continue
                print(f'\n⚠️ {line}')
        
        process.wait()
        
        if process.returncode == 0:
            print('\n\n✅ Загрузка завершена!')
            return True
        else:
            print(f'\n❌ Ошибка загрузки (код: {process.returncode})')
            return False
            
    except KeyboardInterrupt:
        print('\n\n❌ Загрузка отменена')
        if 'process' in locals():
            process.terminate()
        return False
    except Exception as e:
        print(f'\n❌ Ошибка: {e}')
        return False

def main():
    # Создаем папку downloads
    download_dir = Path('downloads')
    download_dir.mkdir(exist_ok=True)
    
    print('╔════════════════════════════════╗')
    print('║     ClipySave  v1.0            ║')
    print('║     by @thetemirbolatov        ║')
    print('╚════════════════════════════════╝')
    
    while True:
        print('\n📁 Файлы сохраняются в папку: downloads/')
        url = input('\n🔗 Вставьте ссылку (или "exit"): ').strip()
        
        if url.lower() in ['exit', 'quit', 'q', 'выход']:
            print('\n👋 До свидания!')
            break
        
        if not url:
            print('❌ Введите ссылку')
            continue
        
        # Переходим в папку downloads
        os.chdir('downloads')
        
        # Скачиваем
        download_media(url)
        
        # Возвращаемся обратно
        os.chdir('..')
        
        print('\n' + '─' * 40)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n👋 Программа завершена')
    except Exception as e:
        print(f'\n❌ Ошибка: {e}')
        input('\nНажмите Enter для выхода...')