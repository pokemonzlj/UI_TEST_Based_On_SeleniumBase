import subprocess
import sys
from datetime import datetime
from utils.logger import setup_logger, get_logger


def run_tests(test_path="test_cases/", report_dir=".", extra_args=None):
    """
    执行UI自动化测试

    Args:
        test_path: 测试用例路径，默认为"test_cases/"
        report_dir: 报告保存目录，默认为当前目录
        extra_args: 额外的pytest参数列表，如["-k", "test_login"]

    Returns:
        int: 测试退出码（0表示成功，非0表示失败）

    使用示例:
        # 基本使用
        run_ui_tests()

        # 指定测试路径
        run_ui_tests(test_path="test_cases/test_login.py")

        # 只运行特定测试
        run_ui_tests(extra_args=["-k", "test_search"])

        # 定时任务使用
        import schedule
        schedule.every().hour.do(run_ui_tests)
    """
    # 初始化logger
    logger = setup_logger('ui_test')

    logger.info("="*70)
    logger.info("🚀 开始执行UI自动化测试")
    logger.info("="*70)

    # 生成带时间戳的报告文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"{report_dir}/report_{timestamp}.html"

    logger.info(f"测试报告将保存为: {report_name}")

    # 构建pytest命令
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "--mobile",
        "--rcs",  # 类级别复用浏览器会话（一个测试类 = 一个浏览器窗口）
        f"--html={report_name}",
        "--self-contained-html",  # 生成独立的HTML文件
        "--tb=short"  # 简短的traceback（需要堆栈信息来提取错误位置）
    ]

    # 添加额外参数
    if extra_args:
        cmd.extend(extra_args)

    logger.info(f"执行命令: {' '.join(cmd)}")
    logger.info("="*70)

    # 执行测试 - 捕获pytest的输出，只显示我们自己的日志
    # 使用utf-8编码，避免Windows上的编码问题
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'  # 遇到无法解码的字符时用?替换，而不是抛出异常
    )

    # 过滤输出 - 只显示我们关心的内容
    output_lines = result.stdout.split('\n')
    in_our_section = False  # 标记是否在我们的输出区域

    for line in output_lines:
        # 检测到我们的统计信息开始
        if '📊 测试结果统计' in line:
            in_our_section = True

        # 如果在我们的输出区域，显示所有内容
        if in_our_section:
            # 跳过pytest自己的summary
            if 'short test summary' in line or 'FAILED test_cases' in line or 'failed in' in line:
                continue
            print(line)
            continue

        # 不在我们的区域，跳过pytest的输出
        if any(skip in line for skip in [
            'test session starts',
            'platform darwin',
            'cachedir:',
            'rootdir:',
            'plugins:',
            'asyncio:',
            'collecting',
            'collected',
            'FAILURES',
            '/opt/homebrew/',
            'Stacktrace:',
            'chromedriver',
            'libsystem',
            'selenium.common',
            'seleniumbase.common',
            'Message:',
            'Element {'
        ]):
            continue

        # 跳过pytest的错误堆栈
        if line.strip().startswith('E   '):
            continue

    logger.info("="*70)
    if result.returncode == 0:
        logger.info("✅ 所有测试通过")
    else:
        logger.warning(f"⚠️  测试完成，退出码: {result.returncode}")
    logger.info("="*70)

    return result.returncode


if __name__ == "__main__":
    # 直接调用封装好的测试函数
    exit_code = run_tests()
    sys.exit(exit_code)