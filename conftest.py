import pytest
import requests
import os
import traceback
import json
import sys
from datetime import datetime
from pathlib import Path
from selenium import webdriver

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger

# 获取logger实例
logger = get_logger()

# 全局统计数据
test_stats = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'error': 0,
    'skipped': 0,
    'failed_cases': [],
    'report_file': '',  # 存储报告文件名
    'report_files': []  # 存储报告文件列表
}


def extract_real_error_location(report):
    """
    从测试报告中提取真实的错误位置

    策略：找到test_cases目录下第一个非test_函数的位置

    Args:
        report: pytest测试报告对象

    Returns:
        dict: 包含真实错误位置的字典
    """
    real_location = {
        'file': '',
        'function': '',
        'line': 0,
        'code': ''
    }

    if not report.longrepr:
        return real_location

    try:
        # 获取异常信息
        longrepr_str = str(report.longrepr)

        # 解析堆栈信息 - 查找所有test_cases目录下的帧
        lines = longrepr_str.split('\n')

        # 存储找到的所有test_cases相关的帧
        test_cases_frames = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 查找test_cases目录下的文件 - 兼容Windows和Unix路径
            if ('test_cases/' in line or 'test_cases\\' in line) and '.py:' in line:
                # 提取文件路径和行号
                try:
                    # 格式: test_cases/test_SAAS_user_master.py:173: in buy_goods_in_detail_page
                    parts = line.split(':')
                    if len(parts) >= 3:
                        file_part = parts[0].strip()
                        line_num = int(parts[1].strip())

                        # 提取函数名
                        func_name = ''
                        if 'in ' in line:
                            func_name = line.split('in ')[-1].strip()

                        # 查找代码行（通常在下一行或下两行）
                        code_line = ''
                        for j in range(i+1, min(i+3, len(lines))):
                            stripped = lines[j].strip()
                            # 跳过空行、File开头的行、以及分隔符行（如 _ _ _ _）
                            if stripped and not stripped.startswith('File') and not all(c in '_ ' for c in stripped):
                                code_line = stripped
                                break

                        # 提取文件名 - 兼容Windows和Unix路径
                        file_name = os.path.basename(file_part)

                        test_cases_frames.append({
                            'file': file_name,
                            'function': func_name,
                            'line': line_num,
                            'code': code_line
                        })
                except Exception as e:
                    logger.debug(f"解析帧时出错: {str(e)}")

            i += 1

        # 从找到的帧中选择真实错误位置
        # 对于 AssertionError，优先显示测试代码中调用断言的位置
        # 而不是断言方法内部的 raise 语句位置

        # 检查是否是 AssertionError
        is_assertion_error = 'AssertionError' in str(report.longrepr)

        if is_assertion_error and len(test_cases_frames) >= 2:
            # 对于断言错误，选择倒数第二个帧（调用断言方法的位置）
            # 最后一个帧通常是 operations.py 中的 raise AssertionError
            # 倒数第二个帧是测试代码中调用 assert_element_exists 等方法的位置
            for frame in reversed(test_cases_frames[:-1]):
                if frame['function']:
                    real_location = frame
                    break
        else:
            # 非断言错误，优先选择非test_函数的帧
            for frame in test_cases_frames:
                if frame['function'] and not frame['function'].startswith('test_'):
                    real_location = frame
                    break

        # 如果没有找到合适的帧，使用第一个test_cases的帧
        if not real_location['function'] and test_cases_frames:
            real_location = test_cases_frames[0]

    except Exception as e:
        logger.debug(f"解析错误位置时出错: {str(e)}")

    return real_location


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """收集每个测试的执行结果"""
    outcome = yield
    report = outcome.get_result()

    # 只统计测试执行阶段（call），不统计setup/teardown
    if report.when == 'call':
        test_stats['total'] += 1

        if report.passed:
            test_stats['passed'] += 1
            logger.info(f"✅ 测试通过: {item.nodeid}")
        elif report.failed:
            test_stats['failed'] += 1

            # 提取真实错误位置
            real_location = extract_real_error_location(report)

            # 构建错误位置信息
            if real_location['function']:
                location_str = f"{real_location['file']}::{real_location['function']} (第{real_location['line']}行)"
            else:
                location_str = f"{item.location[0]}::{item.location[2]} (第{item.location[1] + 1}行)"

            # 清理错误信息 - 移除pytest的格式化标记
            error_str = str(report.longrepr)
            # 移除 "E   " 前缀
            error_lines = []
            for line in error_str.split('\n'):
                if line.strip().startswith('E   '):
                    error_lines.append(line.replace('E   ', '').strip())
                elif not any(skip in line for skip in [
                    '/opt/homebrew/',
                    'Stacktrace:',
                    'chromedriver',
                    'libsystem'
                ]):
                    error_lines.append(line.strip())

            clean_error = '\n'.join(error_lines)[:300]  # 截取前300字符

            # 记录失败详情
            error_info = {
                'name': item.nodeid,
                'location': location_str,
                'line': real_location['line'] if real_location['line'] else item.location[1] + 1,
                'error': clean_error,
                'real_function': real_location['function'],
                'real_code': real_location['code']
            }

            test_stats['failed_cases'].append(error_info)

            # 记录错误日志（简洁格式）
            line_num = real_location['line'] if real_location['line'] else item.location[1] + 1
            logger.error(f"❌ 测试失败: {item.nodeid} (第{line_num}行)")
            # 只显示非test_函数的业务方法
            if real_location['function'] and not real_location['function'].startswith('test_'):
                logger.error(f"   in {real_location['function']}")
            if real_location['code']:
                logger.error(f"   {real_location['code']}")

        elif report.outcome == 'skipped':
            test_stats['skipped'] += 1
            logger.info(f"⏭️  测试跳过: {item.nodeid}")


def build_report_content(test_stats):
    """构建测试报告内容（markdown）"""
    content = f"""## 🧪 UI自动化测试报告

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 测试结果统计
- 📝 总运行条数: **{test_stats['total']}**
- ✅ 成功条数: **{test_stats['passed']}**
- ❌ 失败条数: **{test_stats['failed']}**
- ⏭ 跳过条数: **{test_stats['skipped']}**
"""

    # 添加失败用例详情
    if test_stats['failed'] > 0:
        content += "\n### ❌ 失败用例详情\n"

        # 按文件分组
        from collections import defaultdict
        cases_by_file = defaultdict(list)
        for case in test_stats['failed_cases']:
            # 提取文件名（不含路径和扩展名）- 兼容Windows和Unix路径
            file_path = case['name'].split('::')[0]
            file_name = os.path.basename(file_path).replace('.py', '')
            cases_by_file[file_name].append(case)

        # 按文件输出
        case_num = 1
        for file_name, cases in cases_by_file.items():
            content += f"\n**📄 测试文件: {file_name}**\n"
            for case in cases:
                # 简化用例名（只保留测试方法名）
                test_name = case['name'].split('::')[-1]
                content += f"\n**{case_num}. {test_name} (第{case['line']}行)**\n"

                # 显示错误信息
                error_msg = case['error']

                # 对于 AssertionError，只显示错误信息（自定义的错误描述）
                if 'AssertionError:' in error_msg:
                    # 提取 AssertionError 后面的自定义错误信息
                    custom_msg = error_msg.split('AssertionError:')[-1].strip()
                    if custom_msg:
                        content += f"- `{custom_msg}`\n"
                # 对于其他错误，显示代码行或函数名
                else:
                    if case.get('real_code'):
                        content += f"- `{case['real_code']}`\n"
                    elif case.get('real_function') and not case['real_function'].startswith('test_'):
                        content += f"- in `{case['real_function']}`\n"

                    # 显示错误类型和详细信息
                    if 'Exception' in error_msg:
                        error_type = error_msg.split(':')[0].split('.')[-1]
                        error_detail = error_msg.split('Message:')[-1].strip() if 'Message:' in error_msg else ''
                        if error_detail:
                            content += f"- 错误: {error_type} - {error_detail[:80]}\n"
                        else:
                            content += f"- 错误: {error_type}\n"

                case_num += 1

    report_files = test_stats.get('report_files', [])
    report_file = test_stats.get('report_file')
    if report_files or report_file:
        content += "\n### 📄 测试报告\n"
        if report_file:
            content += f"文件: `{report_file}`\n"
        if report_files:
            for file_name in report_files:
                content += f"- `{file_name}`\n"

    return content


def send_to_wecom(test_stats):
    """发送测试结果到企业微信"""
    webhook_url = os.getenv('WECOM_WEBHOOK_URL')

    # check if we should skip sending wecom message
    if os.getenv('SKIP_WECOM'):
        return

    if not webhook_url:
        print("\n⚠️  未配置企业微信Webhook URL，跳过发送")
        print("   提示: 设置环境变量 WECOM_WEBHOOK_URL 来启用企微通知")
        return

    content = build_report_content(test_stats)

    # 构建企业微信消息体
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print("\n✅ 测试结果已发送到企业微信")
            else:
                print(f"\n❌ 企业微信返回错误: {result.get('errmsg')}")
        else:
            print(f"\n❌ 发送失败，HTTP状态码: {response.status_code}")
    except Exception as e:
        print(f"\n❌ 发送到企业微信失败: {str(e)}")


def write_test_stats(stats, stats_file):
    """将测试统计信息写入文件（JSON）"""
    if not stats_file:
        return
    os.makedirs(os.path.dirname(stats_file), exist_ok=True)
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """在测试结束后输出统计信息，框架钩子函数，允许用户在测试会话结束时自定义终端输出或收集测试结果。
    这个函数在测试执行完成后被调用，可以用于生成自定义报告、统计信息或执行清理操作。"""
    print("\n" + "="*70)
    print("📊 测试结果统计")
    print("="*70)
    print(f"📝 总运行条数: {test_stats['total']}")
    print(f"✅ 成功条数: {test_stats['passed']}")
    print(f"❌ 失败条数: {test_stats['failed']}")
    print(f"⏭ 跳过条数: {test_stats['skipped']}")

    if test_stats['failed'] > 0:
        print("\n" + "-"*70)
        print("❌ 失败用例详情:")
        print("-"*70)

        # 按文件分组
        from collections import defaultdict
        cases_by_file = defaultdict(list)
        for case in test_stats['failed_cases']:
            # 提取文件名（不含路径和扩展名）- 兼容Windows和Unix路径
            file_path = case['name'].split('::')[0]
            file_name = os.path.basename(file_path).replace('.py', '')
            cases_by_file[file_name].append(case)

        # 按文件输出
        case_num = 1
        for file_name, cases in cases_by_file.items():
            print(f"\n📄 测试用例集: {file_name}")
            for case in cases:
                # 简化用例名（只保留测试方法名）
                test_name = case['name'].split('::')[-1]
                print(f"\n{case_num}. 用例名: {test_name} (第{case['line']}行)")

                # 显示错误信息
                error_msg = case['error']

                # 对于 AssertionError，只显示错误信息（自定义的错误描述）
                if 'AssertionError:' in error_msg:
                    # 提取 AssertionError 后面的自定义错误信息
                    custom_msg = error_msg.split('AssertionError:')[-1].strip()
                    if custom_msg:
                        print(f"   {custom_msg}")
                # 对于其他错误，显示代码行或函数名
                else:
                    if case.get('real_code'):
                        print(f"   {case['real_code']}")
                    elif case.get('real_function') and not case['real_function'].startswith('test_'):
                        print(f"   in {case['real_function']}")

                    # 显示错误类型和详细信息
                    if 'Exception' in error_msg:
                        error_type = error_msg.split(':')[0].split('.')[-1]
                        error_detail = error_msg.split('Message:')[-1].strip() if 'Message:' in error_msg else ''
                        if error_detail:
                            print(f"   错误: {error_type} - {error_detail[:100]}")
                        else:
                            print(f"   错误: {error_type}")

                case_num += 1

    print("\n" + "="*70)

    stats_file = os.getenv('TEST_STATS_FILE')
    if stats_file:
        write_test_stats(test_stats, stats_file)

    if os.getenv('MERGE_TEST_STATS') == '1':
        return

    # 发送到企业微信
    send_to_wecom(test_stats)


def pytest_configure(config):
    """配置报告文件名（带时间戳）"""
    if config.option.htmlpath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        htmlpath = config.option.htmlpath
        if htmlpath == 'report.html':
            report_name = f'report_{timestamp}.html'
            config.option.htmlpath = report_name
            # 保存报告文件名到全局变量
            test_stats['report_file'] = report_name
            test_stats['report_files'].append(report_name)

