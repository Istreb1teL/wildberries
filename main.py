import time
from web import WildberriesParser
from excel import ExcelExporter
import random


def main():

    #start_time = time.time()
    parser = None

    try:
        parser = WildberriesParser(headless=False)
        exporter = ExcelExporter()

        search_query = "пальто из натуральной шерсти"

        # Сбор товаров
        all_products = parser.search_products(search_query, max_pages=3)

        if not all_products:
            return

        # Получаем детальную информацию по товарам
        enriched_products = []

        for i, product in enumerate(all_products, 1):
            if product.get('url'):
                details = parser.get_product_details(product['url'])

                product['description'] = details.get('description', '')
                product['characteristics'] = details.get('characteristics', '')
                product['sizes'] = details.get('sizes', '')
                product['total_stock'] = details.get('total_stock', 0)

                if details.get('images'):
                    product['images'] = details.get('images')
                if details.get('seller_name'):
                    product['seller_name'] = details.get('seller_name')
                if details.get('rating'):
                    product['rating'] = details.get('rating')
                if details.get('reviews_count'):
                    product['reviews_count'] = details.get('reviews_count')

            enriched_products.append(product)

            if i < len(all_products):
                time.sleep(random.uniform(2, 3))

        #  Сохранение полного каталога
        if enriched_products:
            full_catalog_file = "full_catalog.xlsx"
            exporter.save_catalog(enriched_products, full_catalog_file)

            # Фильтруем товары для второго файла экселя
            filtered_products = []

            for product in enriched_products:
                rating = product.get('rating', 0)
                price = product.get('price', 0)
                characteristics = product.get('characteristics', '').lower()

                if rating >= 4.5 and price <= 10000:
                    if 'страна производства: россия' in characteristics:
                        filtered_products.append(product)

            #  Сохранение отфильтрованного каталога в эксель
            if filtered_products:
                filtered_file = "filtered_catalog.xlsx"
                exporter.save_catalog(filtered_products, filtered_file)
            else:
                filtered_file = "filtered_catalog.xlsx"
                exporter.save_catalog([], filtered_file)

           # elapsed_time = time.time() - start_time

    except Exception as e:
        print(f"Произошла ошибка: {e}")

    finally:
        if parser:
            parser.close()


if __name__ == "__main__":
    main()