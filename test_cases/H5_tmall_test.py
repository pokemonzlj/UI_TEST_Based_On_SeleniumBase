import random
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

class EcommerceStoreTest(BaseCase, Operations):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    @safe_execute
    def test_search(self):
        # 打开测试商城首页
        url = "https://tmail.com"
        self.open(url)

        # 等待页面加载完成
        self.wait_for_element_visible("#page-body")

        # 验证页面标题
        self.assert_title_contains("天猫")

if __name__ == "__main__":
    pass