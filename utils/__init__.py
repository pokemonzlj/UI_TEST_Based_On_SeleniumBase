"""
UI自动化测试工具模块
"""

from .logger import get_logger, setup_logger
from .decorators import safe_execute

__all__ = ['get_logger', 'setup_logger', 'safe_execute']

