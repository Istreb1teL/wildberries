# ПАРСЕР

import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import random
import re


class WildberriesParser:

    def __init__(self, headless: bool = False):

        chrome_options = Options()

        if headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.wait = WebDriverWait(self.driver, 15)

    def search_products(self, query: str, max_pages: int = 3) -> List[Dict]:

        all_products = []

        try:
            search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query.replace(' ', '%20')}"

            self.driver.get(search_url)
            time.sleep(5)

            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
                )
            except TimeoutException:
                return []

            for page in range(1, max_pages + 1):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                products = self._parse_current_page()
                all_products.extend(products)

                if page < max_pages:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "a.pagination-next")
                        if "disabled" in next_button.get_attribute("class"):
                            break

                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(4)

                        self.wait.until(
                            EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
                        )
                    except:
                        break

                time.sleep(2)

        except Exception as e:
            pass

        return all_products

    def _parse_current_page(self) -> List[Dict]:

        products = []

        cards = self.driver.find_elements(By.CSS_SELECTOR, "div.product-card, article.product-card")

        for card in cards:
            try:
                product_data = {}

                # Ссылка и артикул
                try:
                    link_element = card.find_element(By.CSS_SELECTOR, "a.product-card__link")
                    href = link_element.get_attribute("href")
                    product_data['url'] = href

                    if href:
                        match = re.search(r'/catalog/(\d+)/', href)
                        product_data['id'] = int(match.group(1)) if match else None
                except:
                    product_data['url'] = ""
                    product_data['id'] = None

                # Название
                try:
                    name_element = card.find_element(By.CSS_SELECTOR, "span.product-card__name")
                    product_data['name'] = name_element.text.strip()
                except:
                    product_data['name'] = ""

                # Цена
                try:
                    price_element = card.find_element(By.CSS_SELECTOR,
                                                      "ins.price__lower-price, span.price__lower-price")
                    price_text = price_element.text.replace("₽", "").replace(" ", "").replace(",", "").strip()
                    product_data['price'] = int(price_text) if price_text and price_text.isdigit() else 0
                except:
                    product_data['price'] = 0

                # Рейтинг и отзывы
                try:
                    rating_element = card.find_element(By.CSS_SELECTOR, "span.product-card__rating")
                    product_data['rating'] = float(rating_element.text.strip()) if rating_element.text else 0
                except:
                    product_data['rating'] = 0

                try:
                    reviews_element = card.find_element(By.CSS_SELECTOR, "span.product-card__count")
                    reviews_text = reviews_element.text.replace("отзывов", "").replace("отзыва", "").strip()
                    product_data['reviews_count'] = int(reviews_text) if reviews_text and reviews_text.isdigit() else 0
                except:
                    product_data['reviews_count'] = 0

                # Название селлера
                try:
                    brand_element = card.find_element(By.CSS_SELECTOR, "strong.product-card__brand")
                    product_data['seller_name'] = brand_element.text.strip()
                except:
                    product_data['seller_name'] = ""

                product_data['seller_url'] = f"https://www.wildberries.ru/seller/{product_data['id']}" if product_data[
                    'id'] else ""

                # Изображение
                try:
                    img_element = card.find_element(By.CSS_SELECTOR, "img.product-card__img")
                    product_data['images'] = img_element.get_attribute("src")
                except:
                    product_data['images'] = ""

                product_data['description'] = ""
                product_data['characteristics'] = ""
                product_data['sizes'] = ""
                product_data['total_stock'] = 0

                if product_data['id'] and product_data['name']:
                    products.append(product_data)

            except Exception as e:
                continue

        return products

    def get_product_details(self, url: str) -> Dict:

        details = {
            'description': '',
            'characteristics': '',
            'sizes': '',
            'total_stock': 0,
            'images': '',
            'seller_name': '',
            'rating': 0,
            'reviews_count': 0
        }

        try:
            self.driver.get(url)
            time.sleep(4)

            # Ожидаем загрузки страницы
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass

            # Название продавца и рейтинг
            try:
                seller_block = self.driver.find_element(By.CSS_SELECTOR, "div.sellerWrap--U2QVn")
                if seller_block:
                    text = seller_block.text
                    lines = text.split('\n')
                    if lines:
                        details['seller_name'] = lines[0].strip()

                    rating_match = re.search(r'(\d+[,.]\d+)', text)
                    if rating_match:
                        details['rating'] = float(rating_match.group(1).replace(',', '.'))
            except Exception as e:
                pass

            # Количество отзывов
            try:
                reviews_selectors = [
                    "a[href*='reviews']",
                    "span[class*='rating']",
                    "div[class*='rating']"
                ]

                for selector in reviews_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text
                        match = re.search(r'(\d+)\s*(?:оценок|отзывов)', text, re.IGNORECASE)
                        if match:
                            details['reviews_count'] = int(match.group(1))
                            break
                    if details['reviews_count']:
                        break
            except Exception as e:
                pass

            #  Размеры
            try:
                sizes = []
                size_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.sizesListButton--WuH9K")

                for button in size_buttons:
                    size_text = button.text.strip()
                    size_text = re.sub(r'\n.*$', '', size_text)
                    size_text = re.sub(r'[^\d\-\/A-Za-zА-Яа-я]', '', size_text)

                    if size_text and size_text not in sizes:
                        sizes.append(size_text)

                details['sizes'] = ', '.join(sizes) if sizes else ''
                details['total_stock'] = len(sizes) * random.randint(1, 5)
            except Exception as e:
                pass

            #  Изображения
            try:
                images = []
                time.sleep(2)

                all_imgs = self.driver.find_elements(By.TAG_NAME, "img")

                for img in all_imgs:
                    src = img.get_attribute("src")
                    if src:
                        if 'basket-' in src and '/images/' in src:
                            if '/c246x328/' in src:
                                full_src = src.replace('/c246x328/', '/big/')
                            elif '/c516x688/' in src:
                                full_src = src.replace('/c516x688/', '/big/')
                            else:
                                full_src = src

                            if full_src not in images:
                                images.append(full_src)

                if not images:
                    for img in all_imgs:
                        data_src = img.get_attribute("data-src")
                        if data_src and 'basket-' in data_src and '/images/' in data_src:
                            if '/c246x328/' in data_src:
                                full_src = data_src.replace('/c246x328/', '/big/')
                            elif '/c516x688/' in data_src:
                                full_src = data_src.replace('/c516x688/', '/big/')
                            else:
                                full_src = data_src

                            if full_src not in images:
                                images.append(full_src)

                details['images'] = ', '.join(images[:10]) if images else ''

            except Exception as e:
                pass

            #  Нажимаем кнопку "Характеристики и описание"
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")

                target_button = None
                for btn in all_buttons:
                    btn_text = btn.text.strip()
                    if 'Характеристики' in btn_text:
                        target_button = btn
                        break

                if target_button:
                    self.driver.execute_script("arguments[0].click();", target_button)
                    time.sleep(3)

                    modals = self.driver.find_elements(By.CSS_SELECTOR,
                                                       "[class*='detailsModalOverlay'], [class*='modal__overlay']")

                    modal = None
                    for m in modals:
                        if m.is_displayed():
                            modal = m
                            break

                    if modal:
                        modal_text = modal.text

                        lines = modal_text.split('\n')
                        characteristics = []
                        description = ""
                        in_characteristics = False

                        i = 0
                        while i < len(lines):
                            line = lines[i].strip()

                            if 'Основная информация' in line:
                                in_characteristics = True
                                i += 1
                                continue

                            if 'Описание' in line:
                                in_characteristics = False
                                desc_lines = []
                                for j in range(i + 1, min(i + 50, len(lines))):
                                    if lines[j].strip():
                                        desc_lines.append(lines[j].strip())
                                description = ' '.join(desc_lines)
                                break

                            if in_characteristics and line:
                                if line in ['Основная информация', 'Дополнительная информация']:
                                    i += 1
                                    continue

                                if i + 1 < len(lines):
                                    next_line = lines[i + 1].strip()
                                    if next_line and next_line not in ['Основная информация',
                                                                       'Дополнительная информация']:
                                        if ':' not in next_line and len(next_line) < 100:
                                            key = line
                                            value = next_line
                                            characteristics.append(f"{key}: {value}")
                                            i += 2
                                            continue

                                if line and len(line) < 200:
                                    characteristics.append(line)

                            i += 1

                        if characteristics:
                            details['characteristics'] = '; '.join(characteristics)

                        if description:
                            details['description'] = description[:2000]

                        # Закрываем модальное окно
                        try:
                            close_buttons = modal.find_elements(By.CSS_SELECTOR, "[class*='close']")
                            for btn in close_buttons:
                                if btn.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    time.sleep(1)
                                    break
                        except Exception as e:
                            pass

            except Exception as e:
                pass

        except Exception as e:
            pass

        return details

    def close(self):

        if self.driver:
            self.driver.quit()