import json
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, TimeoutException, NoSuchElementException

logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)

class DailyScraperPrices(): 
    def __init__(
        self,
        environment,
        date
    ):
        
        logging.info(f"Starting web scraper for environment {environment}")

        self.environment = environment
        self.date = datetime.now().strftime('%Y-%m-%d') if date == None else date

    def load_categories(self):
        df_categorias = pd.read_csv('./data/entities/categorias.csv')
        df_subcategorias = pd.read_csv('./data/entities/subcategorias.csv')

        df_a_scrapear = pd.merge(left=df_categorias, 
                                 right=df_subcategorias, 
                                 how='outer',
                                 on='url_texto_categorias')
        
        df_a_scrapear['url_a_scrapear'] = np.where(~df_a_scrapear['url_subcategorias'].isna(),
                                                    df_a_scrapear['url_subcategorias'],
                                                    df_a_scrapear['url_categorias'])

        categories = df_a_scrapear['url_a_scrapear'].tolist()

        logging.info('Number of categories: {}'.format(len(categories)))

        try:
            df_categorias_scrapped = pd.read_csv('./data/prices/{}_products_prices.csv'.format(self.date))
            categories_scrapped = df_categorias_scrapped['category'].unique().tolist()
            categories_not_scrapped = [cat for cat in categories if cat not in categories_scrapped]
            logging.info('Categories already scrapped today: {}'.format(len(categories_scrapped)))
        except:
            categories_scrapped = 0
            categories_not_scrapped = categories
            logging.info('Categories already scrapped today: 0')

        return categories_not_scrapped

    def get_prices(self):
        categories_not_scrapped = self.load_categories()
        
        data = {key:{} for key in categories_not_scrapped}
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException)

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument('--blink-settings=imagesEnabled=false')

        for idx, category in enumerate(categories_not_scrapped):
            driver = webdriver.Chrome(options=options)

            info = f'[{idx+1}/{len(categories_not_scrapped)}] {category} '
            logging.info(info)
            driver.get(category)
            
            number_of_products = 0
            try:
                footer = WebDriverWait(driver=driver,
                                        timeout=20,
                                        ignored_exceptions=ignored_exceptions).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'p.text-content')))
                number_of_products = int(footer.text.split()[3])
                number_of_loaded_products = int(footer.text.split()[1])
                #logging.info(info + f'(loaded products={number_of_loaded_products}, total={number_of_products})')
                is_error = False
            except:
                logging.info(info + '(ERROR: category not found)')
                is_error = True
                number_of_products = 1
                continue
            
            if is_error:
                continue
            else:
                while number_of_loaded_products < number_of_products:
                    footer = driver.find_element(By.CSS_SELECTOR, 'p.text-content')
                    driver.execute_script('arguments[0].scrollIntoView({block: "center"});', footer)
                    show_more = driver.find_elements(By.XPATH, "//div[text()='Mostrar más']")
                    if show_more:
                        try:
                            show_more[0].click()
                        except (ElementClickInterceptedException, StaleElementReferenceException):
                            continue
                    number_of_loaded_products = int(footer.text.split()[1])
                    logging.info(info + f'(loaded products={number_of_loaded_products}, total={number_of_products})')
                    time.sleep(2)

                loaded_products = json.loads(driver.find_element(By.CSS_SELECTOR, "body script[type='application/ld+json']").get_attribute('innerText'))['itemListElement']
                products = {'item':[],'price':[]}
                for prod in loaded_products:
                    products['item']  += [prod['item']['name']]
                    products['price'] += [prod['item']['offers']['offers'][0]['price']]

                data[category] = products

            if (idx+1) % 10 == 0:
                logging.info('Temporary saving data')
                df = self.transform_data_prices(data=data)
                df.to_csv('./data/prices/{}_products_prices.csv'.format(self.date), index=False, encoding='utf-8')

            driver.quit()

        return data
        
    def transform_data_prices(self, data):
        data_list = []
        for key, value in data.items():
            if value:
                for i in range(len(value['item'])):
                    record_dict = {
                        'category': key,
                        'item': value['item'][i],
                        'price': value['price'][i]
                    }
                    data_list.append(record_dict)

        df = pd.DataFrame(data_list)
        
        return df
        
    def run(self):
        logging.info(f"Getting prices from website")
        prices = self.get_prices()
        df_prices = self.transform_data_prices(data=prices)

        logging.info(f"Saving data")
        df_prices.to_csv('./data/prices/{}_products_prices.csv'.format(self.date), index=False, encoding='utf-8')

        logging.info(f"Success")


def main():
    """Run the project's main ETL process"""
    
    etl = DailyScraperPrices(
        environment=ENVIRONMENT,
        date=DATE)

    etl.run()


if __name__ == '__main__':

    ENVIRONMENT = 'test'
    DATE = None
    
    main()

        

