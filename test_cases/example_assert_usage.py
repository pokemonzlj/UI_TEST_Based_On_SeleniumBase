"""
示例：如何使用新的断言方法

本文件展示了如何使用 assert_element_exists 等方法来确保测试在元素不存在时失败，
并在测试报告中显示自定义的错误信息。

使用场景：
1. 当需要确保关键元素存在时（如购买按钮、提交按钮等）
2. 当需要在测试报告中显示清晰的错误原因时
3. 当需要测试在元素缺失时立即失败，而不是继续执行时
"""

import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from seleniumbase import BaseCase
from utils.logger import get_logger
from utils.decorators import safe_execute
from operations import Operations

logger = get_logger()


class ExampleAssertUsageTest(BaseCase, Operations):
    """
    示例测试类：演示新断言方法的使用
    """

    def test_example_old_way(self):
        """
        旧方式：使用 is_element_exists 判断
        
        问题：如果元素不存在，测试不会失败，只是跳过后续操作
        """
        logger.info("\n" + "="*70)
        logger.info("示例：旧方式 - 使用 is_element_exists")
        logger.info("="*70)
        
        url = "https://view.zonmind.com/?env=production&preview=1&shop_type=3&business_id=769&platform_id=799#/pages/index/index?"
        self.open(url)
        
        # 旧方式：如果元素不存在，只是不执行点击，测试仍然通过
        if self.is_element_exists(".buy-button"):
            logger.info("找到购买按钮，执行点击")
            self.click(".buy-button")
        else:
            logger.warning("未找到购买按钮，跳过点击操作")
            # 注意：这里测试不会失败！
        
        logger.info("测试继续执行...")

    def test_example_new_way_with_default_message(self):
        """
        新方式1：使用 assert_element_exists（默认错误信息）
        
        优点：如果元素不存在，测试会失败，并显示默认错误信息
        """
        logger.info("\n" + "="*70)
        logger.info("示例：新方式1 - 使用默认错误信息")
        logger.info("="*70)
        
        url = "https://view.zonmind.com/?env=production&preview=1&shop_type=3&business_id=769&platform_id=799#/pages/index/index?"
        self.open(url)
        
        # 新方式：如果元素不存在，测试会失败
        # 使用默认错误信息：元素不存在: .buy-button
        self.assert_element_exists(".buy-button")
        self.click(".buy-button")

    def test_example_new_way_with_custom_message(self):
        """
        新方式2：使用 assert_element_exists（自定义错误信息）
        
        优点：如果元素不存在，测试会失败，并显示自定义的清晰错误信息
        推荐：这是最佳实践！
        """
        logger.info("\n" + "="*70)
        logger.info("示例：新方式2 - 使用自定义错误信息（推荐）")
        logger.info("="*70)
        
        url = "https://view.zonmind.com/?env=production&preview=1&shop_type=3&business_id=769&platform_id=799#/pages/index/index?"
        self.open(url)
        
        # 推荐方式：使用自定义错误信息，让报告更清晰
        self.assert_element_exists(".buy-button", "找不到购买按钮")
        self.click(".buy-button")

    @safe_execute
    def test_example_complete_flow(self):
        """
        完整示例：商品购买流程中使用断言方法
        
        展示如何在实际测试场景中使用各种断言方法
        """
        logger.info("\n" + "="*70)
        logger.info("示例：完整购买流程 - 使用多种断言方法")
        logger.info("="*70)
        
        # 1. 打开商城首页
        url = "https://view.zonmind.com/?env=production&preview=1&shop_type=3&business_id=769&platform_id=799#/pages/index/index?"
        logger.info(f"打开商城首页: {url}")
        self.open(url)
        
        # 2. 断言首页关键元素存在
        logger.info("验证首页关键元素...")
        self.assert_element_is_visible(".uni-scroll-view", "首页未正确加载")
        self.assert_element_exists("ul[title='底部导航']", "底部导航栏未显示")
        
        # 3. 点击分类
        logger.info("点击分类标签...")
        self.assert_element_clickable(".tabBarItemTitle:contains('分类')", "分类标签不可点击")
        self.click(".tabBarItemTitle:contains('分类')")
        time.sleep(1)
        
        # 4. 选择商品分类
        logger.info("选择商品分类...")
        self.assert_element_exists(".category-list", "商品分类列表未加载")
        # 假设选择第一个分类
        self.assert_element_clickable(".category-item:first-child", "商品分类不可点击")
        self.click(".category-item:first-child")
        time.sleep(1)
        
        # 5. 验证商品列表
        logger.info("验证商品列表...")
        self.assert_element_exists(".goods-list", "商品列表未加载")
        
        # 6. 点击第一个商品
        logger.info("点击商品...")
        self.assert_element_clickable(".goods-item:first-child", "商品不可点击")
        self.click(".goods-item:first-child")
        time.sleep(2)
        
        # 7. 验证商品详情页
        logger.info("验证商品详情页...")
        self.assert_element_is_visible(".product-detail", "商品详情页未加载")
        self.assert_element_exists(".product-name", "商品名称未显示")
        self.assert_element_exists(".product-price", "商品价格未显示")
        
        # 8. 验证购买按钮
        logger.info("验证购买按钮...")
        self.assert_element_exists(".buy-button", "找不到购买按钮")
        self.assert_element_clickable(".buy-button", "购买按钮不可点击")
        
        # 9. 点击购买
        logger.info("点击购买按钮...")
        self.click(".buy-button")
        
        logger.info("✅ 购买流程测试完成")


# 使用说明：
"""
运行此示例测试：
    python -m pytest test_cases/example_assert_usage.py -v

对比不同方法：
1. test_example_old_way - 旧方式，元素不存在时测试不会失败
2. test_example_new_way_with_default_message - 新方式，使用默认错误信息
3. test_example_new_way_with_custom_message - 新方式，使用自定义错误信息（推荐）
4. test_example_complete_flow - 完整流程示例

测试报告中的错误显示：
- 旧方式：测试通过（即使元素不存在）
- 新方式（默认）：❌ 测试失败 - 元素不存在: .buy-button
- 新方式（自定义）：❌ 测试失败 - 找不到购买按钮

推荐使用自定义错误信息，让测试报告更清晰易懂！
"""

