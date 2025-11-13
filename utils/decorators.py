"""
装饰器模块 - 提供通用装饰器
"""

import functools
import traceback
import sys
from .logger import get_logger

logger = get_logger()


def safe_execute(func):
    """
    安全执行装饰器 - 捕获异常并记录详细错误信息

    特点:
    1. 自动捕获所有异常
    2. 记录真实的错误位置（我们自己代码中的位置，而非test函数或第三方库）
    3. 记录完整的堆栈信息
    4. 不会静默失败，会重新抛出异常

    使用方法:
        @safe_execute
        def login(self):
            # 业务逻辑
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 获取异常信息
            exc_type, exc_value, exc_tb = sys.exc_info()

            # 提取堆栈信息
            tb_list = traceback.extract_tb(exc_tb)

            # 找到真实的错误位置
            # 策略：找到test_cases目录下的第一个非test_函数的帧
            real_error_frame = None

            for frame in tb_list:
                # 只关注我们自己的代码（test_cases目录）
                if 'test_cases/' in frame.filename:
                    # 跳过test_函数本身，找业务方法
                    if not frame.name.startswith('test_'):
                        real_error_frame = frame
                        break

            # 如果没找到业务方法，可能错误就在test函数中
            # 那就找test_cases目录下的任何帧
            if not real_error_frame:
                for frame in tb_list:
                    if 'test_cases/' in frame.filename:
                        real_error_frame = frame
                        break

            # 如果还是没找到，使用最后一个帧
            if not real_error_frame and tb_list:
                real_error_frame = tb_list[-1]

            # 构建错误信息
            if real_error_frame:
                # 提取文件名（不要完整路径）
                filename = real_error_frame.filename.split('/')[-1]
                error_location = f"{filename}::{real_error_frame.name} (第{real_error_frame.lineno}行)"
                error_code = real_error_frame.line
            else:
                error_location = "未知位置"
                error_code = ""

            # 记录详细错误日志（简洁格式）
            logger.error(f"❌ 函数执行失败")
            logger.error(f"   in {real_error_frame.name if real_error_frame else func.__name__}")
            if error_code:
                logger.error(f"   {error_code}")
            logger.error(f"   错误类型: {exc_type.__name__}")
            logger.error(f"   错误信息: {str(exc_value)}")

            # 重新抛出异常，让pytest能够捕获
            raise

    return wrapper


def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    """
    重试装饰器 - 失败后自动重试
    
    Args:
        max_attempts: 最大尝试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型
    
    使用方法:
        @retry(max_attempts=3, delay=2)
        def unstable_operation(self):
            # 可能失败的操作
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(f"函数 {func.__name__} 第{attempt}次尝试失败，{delay}秒后重试...")
                        logger.warning(f"  错误: {str(e)}")
                        time.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 在{max_attempts}次尝试后仍然失败")
            
            # 所有尝试都失败，抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator


def log_execution(level='INFO'):
    """
    日志记录装饰器 - 记录函数的执行
    
    Args:
        level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    
    使用方法:
        @log_execution(level='INFO')
        def important_operation(self):
            # 业务逻辑
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log_func = getattr(logger, level.lower())
            log_func(f"开始执行: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                log_func(f"执行完成: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"执行失败: {func.__name__} - {str(e)}")
                raise
        
        return wrapper
    return decorator

