import json
import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException

logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)

class DailyScraperPrices():
    def __init__(
        self,
        environment
    ):
        
        logging.info(f"Starting web scraper for environment {environment}")

        self.environment = environment

    def get_prices(self, driver, categories):
        data = {key:{} for key in categories}

        for idx,category in enumerate(categories):
            info = f'[{idx+1}/{len(categories)}] {category} '
            print(info, end='')
            driver.get('https://www.vea.com.ar/' + category)
            
            number_of_products = 0
            while number_of_products == 0:
                footer = WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'p.text-content')))
                number_of_products = int(footer.text.split()[3])
                number_of_loaded_products = int(footer.text.split()[1])
            print(f'(loaded products={number_of_loaded_products}, total={number_of_products})', end='\r')
            
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
                print(info + f'(loaded products={number_of_loaded_products}, total={number_of_products})', end='\r')
                time.sleep(1)

            loaded_products = json.loads(driver.find_element(By.CSS_SELECTOR, "body script[type='application/ld+json']").get_attribute('innerText'))['itemListElement']
            products = {'item':[],'price':[]}
            for prod in loaded_products:
                products['item']  += [prod['item']['name']]
                products['price'] += [prod['item']['offers']['offers'][0]['price']]

            data[category] = products

        return data
        
    def transform_data_prices(self, data):
        data_list = []
        for key, value in data.items():
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
        df_categorias = pd.read_csv('./data/entities/categorias.csv')
        categories = df_categorias['url_categorias'].str.split('.ar/', expand=True)[1].tolist()[:10]

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument('--blink-settings=imagesEnabled=false')

        driver = webdriver.Chrome(options=options)

        logging.info(f"Getting prices from website")
        prices = self.get_prices(driver=driver, 
                                 categories=categories)
        df_prices = self.transform_data_prices(data=prices)

        logging.info(f"Saving data")
        df_prices.to_csv('./data/prices/products_prices.csv', index=False, encoding='utf-8')

        logging.info(f"Success")


def main():
    """Run the project's main ETL process"""
    
    etl = DailyScraperPrices(
        environment=ENVIRONMENT)

    etl.run()


if __name__ == '__main__':

    ENVIRONMENT = 'test'
    
    main()

        

