import logging
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def create_driver(device_name="iPhone X", width=375, height=1000):
    """
    建立模擬手機裝置的 Chrome driver，
    """
    mobile_emulation = {"deviceName": device_name}
    options = Options()
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_experimental_option("detach", True)  # 保持瀏覽器開啟
    # 強制設定視窗大小
    options.add_argument(f"--window-size={width},{height}")
    return webdriver.Chrome(options=options)

def step1_homepage_screenshot(driver):
    """Step 1：打开首页并截图——等到所有关键元件都渲染完毕后再拍照"""
    logging.info("▶️ Start Step 1: 打开首頁並等待元素渲染完成")
    url = "https://www.cathaybk.com.tw/cathaybk/"
    driver.get(url)
    url = "https://www.cathaybk.com.tw/cathaybk/"
    driver.get(url)
    logging.info(f"🌐 已打开：{url}")

    # 等汉堡菜单出现
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.menu-mb-btn-burger"))
    )
    logging.info("✅ 汉堡菜单出现")

    # 等放大镜搜索按钮出现
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "a.bg-contain.cursor-pointer"))
    )
    logging.info("✅ 搜索图标出现")

    # 等首页功能区至少 6 个按钮出现
    WebDriverWait(driver, 20).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#spa-root a.relative.block")) >= 6
    )
    logging.info("✅ 首页功能按钮至少 6 个就绪")
    time.sleep(0.5)
    # 截图
    save_screenshot_overwrite(driver, "step1_home.png")


def step2_credit_card_menu(driver):
    """Step 2：展开“信用卡”菜单并统计子项目"""
    logging.info("▶️ Start Step 2: 展開「信用卡」選單並截图")
    # 点汉堡菜单
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.menu-mb-btn-burger"))
    ).click()
    logging.info("🍔 点击汉堡菜单")
    time.sleep(0.3)
    # 展开“产品介绍”
    expand_menu_if_collapsed(
        driver,
        toggle_selector="div.nav-arrow.text-base.p-5.w-full.iconfont.icon-line-arrow-down",
        active_class="nav-arrow-active",
        expanded_items_selector="div.menu-dropdown-l2-tab",
        menu_name="產品介紹"
    )
    
    # 展开“信用卡”
    expand_menu_if_collapsed(
        driver,
        toggle_selector="div.menu-dropdown-l2-tab",
        active_class="icon-line-boldarrow-left",
        expanded_items_selector="div.menu-dropdown-mb-l3-item.title.block",
        menu_name="信用卡"
    )
    # 统计可见子项
    container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.menu-dropdown-mb-l3-item.title.block"))
    )
    items = container.find_elements(By.XPATH, "following-sibling::a")
    visible = [el for el in items if el.is_displayed()]
    logging.info(f"📝 Step 2 “信用卡”子项共 {len(visible)} 项")
    for el in visible:
        print(" -", el.text)
    # 截图
    save_screenshot_overwrite(driver, "step2_credit_card_menu.png")


def step3_capture_stopped_cards(driver):
    """
    Step 3：點擊「卡片介紹」，滾動到「停發卡」區塊，
    依序點擊 pagination bullets，並對整個「停發卡」區塊做截圖。
    """
    logging.info("▶ Start Step 3: 點擊「卡片介紹」，並截圖所有『停發卡』")

    # 1. 點擊「卡片介紹」
    elem = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH,
            "//a[contains(@class,'relative block cursor-pointer') and contains(text(),'卡片介紹')]"
        ))
    )
    elem.click()
    logging.info("🚀 已點擊「卡片介紹」")

    # 2. 定位「停發卡」區塊的最外層 wrapper
    stopped_wrapper = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH,
            "//div[contains(@class,'cubre-o-block__wrap')"
            " and .//div[contains(@class,'cubre-a-iconTitle__text') and contains(text(),'停發卡')]]"
        ))
    )
    # 將整個區塊置中
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", stopped_wrapper)
    logging.info("✅ 已定位並滾動到「停發卡」區塊")

    # 3. 等待至少一個 bullet 出現
    WebDriverWait(driver, 10).until(
        lambda d: len(stopped_wrapper.find_elements(
            By.CSS_SELECTOR,
            "span.swiper-pagination-bullet"
        )) > 0
    )
    bullets = stopped_wrapper.find_elements(By.CSS_SELECTOR, "span.swiper-pagination-bullet")
    total = len(bullets)
    logging.info(f"🔢 在「停發卡」區塊內共找到 {total} 個 已停發信用卡")

    # 4. 確保 screenshots 目錄存在
    shots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    os.makedirs(shots_dir, exist_ok=True)

    # 5. 依序點 bullet，等待 active，再把整個區塊置中並截圖
    for idx, bullet in enumerate(bullets, start=1):
        # 點 bullet
        bullet.click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                f"span.swiper-pagination-bullet.swiper-pagination-bullet-active[aria-label='Go to slide {idx}']"
            ))
        )
        logging.info(f"📄 已切到第 {idx}/{total} 張卡片")

        # 把「停發卡」區塊置中
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", stopped_wrapper)
        time.sleep(0.2)  # 等動畫穩定

        # 截圖
        save_screenshot_overwrite(driver, f"step3_stopped_card_{idx}.png")


    logging.info("🎉 Step 3 完成：所有停發卡已逐一截圖")



def expand_menu_if_collapsed(driver, toggle_selector, active_class, expanded_items_selector, menu_name, timeout=10):
    """通用：若未展开则点击并等待子项出现"""
    try:
        toggle = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, toggle_selector))
        )
        cls = toggle.get_attribute("class")
        if active_class in cls:
            logging.info(f"📂 『{menu_name}』已展开")
            return
        logging.info(f"📂 『{menu_name}』展开中…")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", toggle)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", toggle)
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_any_elements_located((By.CSS_SELECTOR, expanded_items_selector))
        )
        logging.info(f"✅ 『{menu_name}』展开完成")
        time.sleep(0.3)
    except Exception as e:
        logging.exception(f"❌ 展开『{menu_name}』失败: {e}")

def save_screenshot_overwrite(driver, filename: str):
    """
    在 ./screenshots/ 目录下，以 filename 存图，若同名先删再写入。
    """
    # 1) 构造绝对路径，基于当前工作目录
    screenshots_dir = Path.cwd() / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    dest = screenshots_dir / filename

    # 2) 如果这个文件存在就删掉
    if dest.exists():
        dest.unlink()
        logging.info(f"🗑️ 已删除旧截图：{dest}")

    # 3) 再保存
    driver.save_screenshot(str(dest))
    logging.info(f"📸 新截图已保存（覆盖）：{dest}")
    
    
if __name__ == "__main__":
    driver = create_driver()
    try:
        step1_homepage_screenshot(driver)
        step2_credit_card_menu(driver)
        step3_capture_stopped_cards(driver)
    finally:
        input("🚨 全部步骤完成，按 Enter 结束…")
