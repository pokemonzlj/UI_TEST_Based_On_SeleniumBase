"""
Selenium操作封装类 - Mixin模式

使用方法:
    class YourTestClass(BaseCase, Operations):
        def test_something(self):
            # 使用封装的方法
            if self.is_element_exists(".selector"):
                self.safe_click(".button")
"""

import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from utils.logger import get_logger

logger = get_logger()


class Operations:
    """
        浏览器导航操作
        self.open(url) - 导航到指定URL
        self.go_back() - 返回上一页
        self.get_current_url() - 获取当前页面URL
        self.get_title() - 获取当前页面标题
        self.get_page_source() - 获取当前页面HTML源代码

        元素交互操作
        self.type(selector, text) - 在指定元素输入文本
        self.type("input", "text\n")  # 输入文本后再按下ENTER
        self.click(selector) - 点击指定元素
        self.click_link(link_text) - 点击包含指定文本的链接
        self.select_option_by_text(dropdown_selector, option) - 在下拉菜单中选择指定文本的选项
        self.hover_and_click(hover_selector, click_selector) - 先悬停在指定元素上，再点击另一个元素
        self.drag_and_drop(drag_selector, drop_selector) - 执行拖放操作

        元素状态检查
        self.get_text(selector) - 获取元素文本内容
        self.get_attribute(selector, attribute) - 获取元素属性值
        self.is_element_visible(selector) - 检查元素是否可见
        self.is_text_visible(text, selector) - 检查文本在元素中是否可见
        self.is_element_present(selector) - 检查元素在HTML中存在

        窗口和框架操作
        self.switch_to_frame(frame) - 切换到iframe
        self.switch_to_default_content() - 从iframe切换回主文档
        self.open_new_window() - 打开新窗口
        self.switch_to_window(window) - 切换到指定窗口
        self.switch_to_default_window() - 切换回默认窗口

        驱动和会话管理
        self.get_new_driver(OPTIONS) - 使用指定选项创建新驱动
        self.switch_to_driver(driver) - 切换到指定驱动
        self.switch_to_default_driver() - 切换回默认驱动

        等待和断言
        self.wait_for_element(selector) - 等待元素可见
        self.sleep(seconds) - 强制等待指定秒数
        self.assert_element(selector) - 断言元素可见
        self.assert_text(text, selector) - 断言元素包含指定文本
        self.assert_text(text, selector, timeout=3)  # 在某些秒数内断言页面上元素内文本的可见性
        self.assert_exact_text(text, selector) - 断言元素文本与指定文本完全一致
        self.assert_title(title) - 断言页面标题
        self.assert_downloaded_file(file) - 断言文件已下载
        self.assert_no_404_errors() - 断言没有404错误
        self.assert_no_js_errors() - 断言没有JavaScript错误
        self.assert_equal(var1, var2)  # 断言任何事情，是否相等

        自定义断言方法（元素不存在时测试失败）
        self.assert_element_exists(selector, error_msg) - 断言元素存在，失败时显示自定义错误
        self.assert_element_is_visible(selector, error_msg) - 断言元素可见，失败时显示自定义错误
        self.assert_element_clickable(selector, error_msg) - 断言元素可点击，失败时显示自定义错误
        self.assert_text_in_element(selector, text, error_msg) - 断言元素包含文本，失败时显示自定义错误

        其他操作
        self.save_screenshot(name) - 保存当前页面截图
"""

    def is_element_exists(self, selector, timeout=2):
        """
        判断元素是否存在

        Args:
            selector: CSS选择器
            timeout: 超时时间（秒），默认2秒

        Returns:
            bool: 元素存在返回True，否则返回False
        """
        try:
            self.wait_for_element_present(selector, timeout=timeout)
            return True
        except (NoSuchElementException, TimeoutException):
            logger.debug(f"元素不存在: {selector}")
            return False
        except Exception as e:
            logger.warning(f"查找元素异常: {selector}, 错误: {str(e)}")
            return False

    def is_element_visible(self, selector, timeout=2):
        """
        判断元素是否可见

        Args:
            selector: CSS选择器
            timeout: 超时时间（秒），默认2秒

        Returns:
            bool: 元素可见返回True，否则返回False
        """
        try:
            self.wait_for_element_visible(selector, timeout=timeout)
            return True
        except (NoSuchElementException, TimeoutException):
            logger.debug(f"元素不可见: {selector}")
            return False
        except Exception as e:
            logger.warning(f"检查元素可见性异常: {selector}, 错误: {str(e)}")
            return False

    def safe_click(self, selector, timeout=10, retry=3):
        """
        安全点击元素（带重试机制）

        Args:
            selector: CSS选择器
            timeout: 等待超时时间（秒），默认10秒
            retry: 重试次数，默认3次

        Returns:
            bool: 点击成功返回True，失败返回False
        """
        for attempt in range(retry):
            try:
                logger.debug(f"尝试点击元素: {selector} (第{attempt+1}次)")
                self.wait_for_element_clickable(selector, timeout=timeout)
                self.click(selector)
                logger.debug(f"✅ 成功点击: {selector}")
                return True
            except ElementNotInteractableException:
                logger.warning(f"元素不可交互: {selector}, 尝试滚动到元素位置")
                try:
                    self.scroll_to(selector)
                    time.sleep(0.5)
                    self.click(selector)
                    logger.debug(f"✅ 滚动后成功点击: {selector}")
                    return True
                except Exception as e:
                    if attempt < retry - 1:
                        logger.warning(f"点击失败，1秒后重试: {str(e)}")
                        time.sleep(1)
                    else:
                        logger.error(f"❌ 点击失败（已重试{retry}次）: {selector}, 错误: {str(e)}")
                        return False
            except Exception as e:
                if attempt < retry - 1:
                    logger.warning(f"点击异常，1秒后重试: {str(e)}")
                    time.sleep(1)
                else:
                    logger.error(f"❌ 点击失败（已重试{retry}次）: {selector}, 错误: {str(e)}")
                    return False
        return False

    def safe_type(self, selector, text, timeout=10, clear_first=True):
        """
        安全输入文本

        Args:
            selector: CSS选择器
            text: 要输入的文本
            timeout: 等待超时时间（秒），默认10秒
            clear_first: 是否先清空输入框，默认True

        Returns:
            bool: 输入成功返回True，失败返回False
        """
        try:
            logger.debug(f"尝试输入文本到: {selector}")
            self.wait_for_element_visible(selector, timeout=timeout)

            if clear_first:
                self.clear(selector)
                logger.debug(f"已清空输入框: {selector}")

            self.type(selector, text)
            logger.debug(f"✅ 成功输入文本到: {selector}")
            return True
        except Exception as e:
            logger.error(f"❌ 输入文本失败: {selector}, 错误: {str(e)}")
            return False

    def wait_and_click(self, selector, timeout=10):
        """
        等待元素可见后点击

        Args:
            selector: CSS选择器
            timeout: 等待超时时间（秒），默认10秒

        Returns:
            bool: 点击成功返回True，失败返回False
        """
        try:
            logger.debug(f"等待元素可见: {selector}")
            self.wait_for_element_visible(selector, timeout=timeout)
            self.click(selector)
            logger.debug(f"✅ 等待后成功点击: {selector}")
            return True
        except Exception as e:
            logger.error(f"❌ 等待并点击失败: {selector}, 错误: {str(e)}")
            return False

    def get_text_safe(self, selector, timeout=5, default=""):
        """
        安全获取元素文本

        Args:
            selector: CSS选择器
            timeout: 等待超时时间（秒），默认5秒
            default: 获取失败时的默认值，默认空字符串

        Returns:
            str: 元素文本内容，失败返回default值
        """
        try:
            self.wait_for_element_visible(selector, timeout=timeout)
            text = self.get_text(selector)
            logger.debug(f"获取文本成功: {selector} = '{text}'")
            return text
        except Exception as e:
            logger.warning(f"获取文本失败: {selector}, 错误: {str(e)}, 返回默认值: '{default}'")
            return default

    def wait_for_text_visible(self, text, selector=None, timeout=10):
        """
        等待指定文本出现

        Args:
            text: 要等待的文本内容
            selector: CSS选择器，如果指定则在该元素内查找文本
            timeout: 等待超时时间（秒），默认10秒

        Returns:
            bool: 文本出现返回True，超时返回False
        """
        try:
            if selector:
                logger.debug(f"等待文本'{text}'出现在元素: {selector}")
                self.wait_for_text(text, selector, timeout=timeout)
            else:
                logger.debug(f"等待文本'{text}'出现在页面")
                self.wait_for_text_visible(text, timeout=timeout)
            logger.debug(f"✅ 文本已出现: '{text}'")
            return True
        except Exception as e:
            logger.warning(f"等待文本超时: '{text}', 错误: {str(e)}")
            return False

    def scroll_to_element(self, selector):
        """
        滚动到指定元素

        Args:
            selector: CSS选择器

        Returns:
            bool: 滚动成功返回True，失败返回False
        """
        try:
            logger.debug(f"滚动到元素: {selector}")
            self.scroll_to(selector)
            time.sleep(0.3)  # 等待滚动动画完成
            logger.debug(f"✅ 滚动成功: {selector}")
            return True
        except Exception as e:
            logger.warning(f"滚动失败: {selector}, 错误: {str(e)}")
            return False

    def select_dropdown_option(self, selector, option_text, timeout=10):
        """
        选择下拉框选项（通过文本）

        Args:
            selector: 下拉框CSS选择器
            option_text: 选项文本
            timeout: 等待超时时间（秒），默认10秒

        Returns:
            bool: 选择成功返回True，失败返回False
        """
        try:
            logger.debug(f"选择下拉框选项: {selector} -> '{option_text}'")
            self.wait_for_element_visible(selector, timeout=timeout)
            self.select_option_by_text(selector, option_text)
            logger.debug(f"✅ 选择成功: '{option_text}'")
            return True
        except Exception as e:
            logger.error(f"❌ 选择下拉框选项失败: {selector}, 错误: {str(e)}")
            return False

    def get_element_count(self, selector):
        """
        获取元素个数
        :param selector:
        :return:
        """
        try:
            eles = self.find_elements(selector)
            elements_count = len(eles)
            logger.info(f"找到{elements_count}个指定元素")
            return elements_count
        except (NoSuchElementException, TimeoutException):
            logger.debug(f"元素不存在: {selector}")
            return False
        except Exception as e:
            logger.warning(f"查找元素异常: {selector}, 错误: {str(e)}")
            return False

    def assert_element_exists(self, selector, error_msg=None, timeout=2):
        """
        断言元素存在，如果不存在则测试失败

        Args:
            selector: CSS选择器
            error_msg: 自定义错误信息，如"找不到购买按钮"。如果不提供，使用默认信息
            timeout: 超时时间（秒），默认2秒

        Raises:
            AssertionError: 当元素不存在时抛出，测试将被标记为失败

        使用示例:
            # 使用默认错误信息
            self.assert_element_exists(".buy-button")

            # 使用自定义错误信息
            self.assert_element_exists(".buy-button", "找不到购买按钮")
            self.assert_element_exists(".cart-icon", "购物车图标未显示")
        """
        if not self.is_element_exists(selector, timeout=timeout):
            # 如果没有提供自定义错误信息，使用默认信息
            if error_msg is None:
                error_msg = f"元素不存在: {selector}"

            logger.error(f"❌ 断言失败: {error_msg}")
            raise AssertionError(error_msg)

        logger.debug(f"✅ 元素存在: {selector}")
        return True

    def assert_element_is_visible(self, selector, error_msg=None, timeout=2):
        """
        断言元素可见，如果不可见则测试失败

        注意：此方法名为 assert_element_is_visible，避免与 SeleniumBase 的 assert_element_visible 冲突

        Args:
            selector: CSS选择器
            error_msg: 自定义错误信息，如"商品详情页未加载"。如果不提供，使用默认信息
            timeout: 超时时间（秒），默认2秒

        Raises:
            AssertionError: 当元素不可见时抛出，测试将被标记为失败

        使用示例:
            # 使用默认错误信息
            self.assert_element_is_visible(".product-detail")

            # 使用自定义错误信息
            self.assert_element_is_visible(".product-detail", "商品详情页未加载")
            self.assert_element_is_visible(".price", "价格信息未显示")
        """
        # 直接使用 wait_for_element_visible 来避免方法名冲突
        try:
            self.wait_for_element_visible(selector, timeout=timeout)
            logger.debug(f"✅ 元素可见: {selector}")
            return True
        except (NoSuchElementException, TimeoutException):
            # 如果没有提供自定义错误信息，使用默认信息
            if error_msg is None:
                error_msg = f"元素不可见: {selector}"

            logger.error(f"❌ 断言失败: {error_msg}")
            raise AssertionError(error_msg)
        except Exception as e:
            # 如果没有提供自定义错误信息，使用默认信息
            if error_msg is None:
                error_msg = f"检查元素可见性异常: {selector}"

            logger.error(f"❌ 断言失败: {error_msg}, 错误: {str(e)}")
            raise AssertionError(error_msg) from e

    def assert_element_clickable(self, selector, error_msg=None, timeout=10):
        """
        断言元素可点击，如果不可点击则测试失败

        Args:
            selector: CSS选择器
            error_msg: 自定义错误信息，如"提交按钮不可点击"。如果不提供，使用默认信息
            timeout: 超时时间（秒），默认10秒

        Raises:
            AssertionError: 当元素不可点击时抛出，测试将被标记为失败

        使用示例:
            # 使用默认错误信息
            self.assert_element_clickable(".submit-button")

            # 使用自定义错误信息
            self.assert_element_clickable(".submit-button", "提交按钮不可点击")
            self.assert_element_clickable(".confirm-btn", "确认按钮未激活")
        """
        try:
            self.wait_for_element_clickable(selector, timeout=timeout)
            logger.debug(f"✅ 元素可点击: {selector}")
            return True
        except (NoSuchElementException, TimeoutException) as e:
            # 如果没有提供自定义错误信息，使用默认信息
            if error_msg is None:
                error_msg = f"元素不可点击: {selector}"

            logger.error(f"❌ 断言失败: {error_msg}")
            raise AssertionError(error_msg) from e
        except Exception as e:
            # 如果没有提供自定义错误信息，使用默认信息
            if error_msg is None:
                error_msg = f"检查元素可点击性异常: {selector}"

            logger.error(f"❌ 断言失败: {error_msg}, 错误: {str(e)}")
            raise AssertionError(error_msg) from e

    def assert_text_in_element(self, selector, expected_text, error_msg=None, timeout=5):
        """
        断言元素包含指定文本，如果不包含则测试失败

        Args:
            selector: CSS选择器
            expected_text: 期望的文本内容
            error_msg: 自定义错误信息，如"商品名称不正确"。如果不提供，使用默认信息
            timeout: 超时时间（秒），默认5秒

        Raises:
            AssertionError: 当元素不包含指定文本时抛出，测试将被标记为失败

        使用示例:
            # 使用默认错误信息
            self.assert_text_in_element(".product-name", "测试商品")

            # 使用自定义错误信息
            self.assert_text_in_element(".product-name", "测试商品", "商品名称不正确")
            self.assert_text_in_element(".price", "¥", "价格格式错误")
        """
        try:
            actual_text = self.get_text_safe(selector, timeout=timeout)

            if expected_text not in actual_text:
                # 如果没有提供自定义错误信息，使用默认信息
                if error_msg is None:
                    error_msg = f"元素文本不匹配: 期望包含'{expected_text}', 实际为'{actual_text}'"

                logger.error(f"❌ 断言失败: {error_msg}")
                raise AssertionError(error_msg)

            logger.debug(f"✅ 文本匹配: {selector} 包含 '{expected_text}'")
            return True
        except AssertionError:
            # 重新抛出AssertionError
            raise
        except Exception as e:
            # 如果没有提供自定义错误信息，使用默认信息
            if error_msg is None:
                error_msg = f"检查元素文本异常: {selector}"

            logger.error(f"❌ 断言失败: {error_msg}, 错误: {str(e)}")
            raise AssertionError(error_msg) from e
