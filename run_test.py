import subprocess
import sys
import os
import threading
import json
from datetime import datetime
from utils.logger import setup_logger, get_logger
from conftest import send_to_wecom, build_report_content


def run_test_batch(files, mode, timestamp, report_dir, extra_args, exit_codes, index, stats_file):
    """在线程中执行测试批次

    Args:
        files: 测试文件列表
        mode: 'mobile' 或 'desktop'
        timestamp: 时间戳
        report_dir: 报告目录
        extra_args: 额外的 pytest 参数
        exit_codes: 用于存储退出码的列表
        index: 在 exit_codes 列表中的索引
    """
    logger = get_logger()

    if mode == 'mobile':
        logger.info(f"📱 正在执行移动端模式测试 ({len(files)} 个文件)")
        report_name = f"{report_dir}/report_{timestamp}_mobile.html"

        cmd = [sys.executable, "-m", "pytest"] + files + [
            "--rcs",
            f"--html={report_name}",
            "--self-contained-html",
            "--tb=short",
            "--mobile",
            "--window-size=500,844"
        ]
    else:  # desktop
        logger.info(f"🖥️  正在执行桌面模式测试 ({len(files)} 个文件)")
        report_name = f"{report_dir}/report_{timestamp}_desktop.html"

        cmd = [sys.executable, "-m", "pytest"] + files + [
            "--rcs",
            f"--html={report_name}",
            "--self-contained-html",
            "--tb=short"
        ]

    if extra_args:
        cmd.extend(extra_args)

    logger.info(f"测试报告: {report_name}")

    # 执行测试
    env = os.environ.copy()
    env['TEST_STATS_FILE'] = stats_file
    env['MERGE_TEST_STATS'] = '1'
    env('WECOM_WEBHOOK_URL') = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e"
    exit_code = run_pytest_subprocess(cmd, logger, env=env)
    exit_codes[index] = exit_code

    logger.info(f"{'📱 移动端' if mode == 'mobile' else '🖥️  桌面端'}测试完成")


def find_test_files(path):
    """Recursively find all python test files in a directory"""
    test_files = []
    if os.path.isfile(path):
        return [path]

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py") and (file.startswith("test_") or file.endswith("_test.py")):
                test_files.append(os.path.join(root, file))
    return test_files

def run_pytest_subprocess(cmd, logger, env=None):
    """Helper to run pytest subprocess and log output"""
    logger.info(f"执行命令: {' '.join(cmd)}")
    logger.info("="*70)

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env
    )

    output_lines = result.stdout.split('\n')
    in_our_section = True

    for line in output_lines:
        if '📊 测试结果统计' in line:
            in_our_section = True

        if in_our_section:
            if 'short test summary' in line or 'FAILED test_cases' in line or 'failed in' in line:
                continue
            print(line)
            continue

        if any(skip in line for skip in [
            'test session starts', 'platform darwin', 'cachedir:', 'rootdir:', 'plugins:',
            'asyncio:', 'collecting', 'collected', 'FAILURES', '/opt/homebrew/',
            'Stacktrace:', 'chromedriver', 'libsystem', 'selenium.common',
            'seleniumbase.common', 'Message:', 'Element {'
        ]):
            continue

        if line.strip().startswith('E   '):
            continue

    return result.returncode

def run_tests(test_path="test_cases/", report_dir=".", extra_args=None, mobile_mode=None):
    """
    执行UI自动化测试

    Args:
        test_path: 测试用例路径，默认为"test_cases/"
        report_dir: 报告保存目录，默认为当前目录
        extra_args: 额外的pytest参数列表
        mobile_mode: 是否开启移动端模式。
                     None(默认): 自动根据文件名包含 "_H5" 分组运行
                     True: 强制所有用例以移动端模式运行
                     False: 强制所有用例以桌面模式运行
    """
    logger = setup_logger('ui_test')

    logger.info("="*70)
    logger.info("🚀 开始执行UI自动化测试")

    # 1. Determine files to run
    all_files = find_test_files(test_path)
    if not all_files:
        logger.warning(f"⚠️  未找到测试文件: {test_path}")
        return 1

    # 2. Group files
    mobile_files = []
    desktop_files = []

    if mobile_mode is True:
        mobile_files = all_files
    elif mobile_mode is False:
        desktop_files = all_files
    else:
        # Auto-detect
        for f in all_files:
            if "_H5" in os.path.basename(f) or "_mobile" in os.path.basename(f):
                mobile_files.append(f)
            else:
                desktop_files.append(f)

    exit_codes = [0, 0]  # [mobile_exit_code, desktop_exit_code]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    threads = []
    stats_files = []

    # 3. 创建并启动移动端测试线程
    if mobile_files:
        mobile_stats_file = f"{report_dir}/stats_{timestamp}_mobile.json"
        stats_files.append(mobile_stats_file)
        mobile_thread = threading.Thread(
            target=run_test_batch,
            args=(mobile_files, 'mobile', timestamp, report_dir, extra_args, exit_codes, 0, mobile_stats_file)
        )
        threads.append(mobile_thread)
        mobile_thread.start()
        logger.info(f"📱 移动端测试线程已启动 ({len(mobile_files)} 个文件)")

    # 4. 创建并启动桌面端测试线程
    if desktop_files:
        desktop_stats_file = f"{report_dir}/stats_{timestamp}_desktop.json"
        stats_files.append(desktop_stats_file)
        desktop_thread = threading.Thread(
            target=run_test_batch,
            args=(desktop_files, 'desktop', timestamp, report_dir, extra_args, exit_codes, 1, desktop_stats_file)
        )
        threads.append(desktop_thread)
        desktop_thread.start()
        logger.info(f"🖥️  桌面端测试线程已启动 ({len(desktop_files)} 个文件)")

    # 5. 等待所有线程完成
    logger.info("⏳ 等待所有测试线程完成...")
    for thread in threads:
        thread.join()

    logger.info("="*70)
    merged_stats = merge_test_stats(stats_files, logger)
    if merged_stats:
        merged_report = f"{report_dir}/report_{timestamp}_merged.md"
        merged_stats['report_file'] = os.path.basename(merged_report)
        merged_stats['report_files'] = merged_stats.get('report_files', [])
        with open(merged_report, 'w', encoding='utf-8') as f:
            f.write(build_report_content(merged_stats))
        send_to_wecom(merged_stats)

    final_exit_code = max(exit_codes) if exit_codes else 0
    if final_exit_code == 0:
        logger.info("✅ 所有测试批次执行完成")
    else:
        logger.warning(f"⚠️  测试执行完成，存在失败 (退出码: {final_exit_code})")
    logger.info("="*70)

    return final_exit_code


def merge_test_stats(stats_files, logger):
    """合并多个测试统计结果"""
    if not stats_files:
        return None

    merged = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'error': 0,
        'skipped': 0,
        'failed_cases': [],
        'report_files': []
    }

    for stats_file in stats_files:
        if not os.path.exists(stats_file):
            logger.warning(f"⚠️  未找到统计文件: {stats_file}")
            continue
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)

        merged['total'] += stats.get('total', 0)
        merged['passed'] += stats.get('passed', 0)
        merged['failed'] += stats.get('failed', 0)
        merged['error'] += stats.get('error', 0)
        merged['skipped'] += stats.get('skipped', 0)
        merged['failed_cases'].extend(stats.get('failed_cases', []))

        report_file = stats.get('report_file')
        if report_file:
            merged['report_files'].append(report_file)
        for file_name in stats.get('report_files', []):
            if file_name not in merged['report_files']:
                merged['report_files'].append(file_name)

    return merged

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
