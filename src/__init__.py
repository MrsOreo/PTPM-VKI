# -*- coding: utf-8 -*-
"""Пакет с модулями лабораторной работы: база данных и веб-парсер."""

from .database import DatabaseRepository
from .parser import ForumParser

__all__ = ["DatabaseRepository", "ForumParser"]
