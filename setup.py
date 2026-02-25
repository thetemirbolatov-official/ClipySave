#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup script for ClipySave - Video Downloader Library
Author: @thetemirbolatov
Company: MIRAJE X
Year: 2026
Version: 1.0.0
"""

from setuptools import setup, find_packages
import os
import sys
from pathlib import Path

# Информация о пакете
VERSION = "1.0.0"
AUTHOR = "thetemirbolatov"
AUTHOR_EMAIL = "thetemirbolatov@mirajex.com"
DESCRIPTION = "Universal Video Downloader for YouTube, Instagram, and VK"

# Читаем README.md
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = DESCRIPTION

# Зависимости
install_requires = [
    "yt-dlp>=2023.0.0",
    "instaloader>=4.9.0",
    "requests>=2.28.0",
]

if sys.platform == "win32":
    install_requires.append("pywin32>=300")

setup(
    # Основная информация
    name="ClipySave",
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # URL
    url="https://github.com/thetemirbolatov-official/ClipySave",
    
    # Социальные сети
    project_urls={
        "GitHub": "https://github.com/thetemirbolatov-official",
        "Instagram": "https://instagram.com/thetemirbolatov",
        "VK": "https://vk.com/thetemirbolatov",
        "Telegram": "https://t.me/thetemirbolatov",
        "Bug Tracker": "https://github.com/thetemirbolatov-official/ClipySave/issues",
    },
    
    # Пакеты
    packages=find_packages(),
    py_modules=["video_downloader", "clipy_save"],
    
    # Зависимости
    install_requires=install_requires,
    
    # Классификаторы
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: Other/Proprietary License",
        "Natural Language :: Russian",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries",
    ],
    
    # Ключевые слова
    keywords="youtube instagram vk downloader video download clipysave",
    
    # Python версия
    python_requires=">=3.7",
    
    # Точки входа
    entry_points={
        "console_scripts": [
            "clipy-save=clipy_save:main_cli",
        ],
    },
    
    # Инклюды
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.ico"],
    },
    
    # Лицензия
    license="Proprietary",
)

print("\n" + "="*50)
print("ClipySave v1.0.0 - MIRAJE X 2026")
print("by @thetemirbolatov")
print("="*50 + "\n")