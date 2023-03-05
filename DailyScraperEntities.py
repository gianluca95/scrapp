import json
import time
import logging
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)

class DailyScraperEntities():
    def __init__(
        self,
        url_main,
        environment,
        time_wait
    ):
        
        logging.info(f"Starting web scraper for environment {environment}")

        self.url_main = url_main
        self.environment = environment
        self.time_wait = time_wait

    def get_main_entities(self, url, driver, time_wait):
        driver.get(url)
        time.sleep(time_wait)
        html_main = BeautifulSoup(driver.page_source, 'html5lib')
        json_main = html_main.find_all('template', {'data-field': 'extensions', 
                                                    'data-type': 'json', 
                                                    'data-varname': '__RUNTIME__'})
        df_main_entities = pd.json_normalize(json.loads(json_main[0].contents[1].string)['store.home/$after_footer/footer-layout.desktop/footer-oculto']['content']['opciones'])
        
        return df_main_entities
    
    def get_entity_marcas(self, df_main_entities):
        df_marcas = df_main_entities[df_main_entities['correspondeA']=='MARCAS'].reset_index(drop=True)
        df_marcas.columns = ['corresponde_a', 'texto_marcas', 'url_marcas']
        return df_marcas

    def get_entity_productos(self, df_main_entities):
        df_productos = df_main_entities[df_main_entities['correspondeA']=='PRODUCTOS'].reset_index(drop=True)
        df_productos.columns = ['corresponde_a', 'texto_productos', 'url_productos']
        return df_productos

    def get_entity_departamentos(self, df_main_entities):
        df_departamentos = df_main_entities[df_main_entities['correspondeA']=='DEPARTAMENTO'].reset_index(drop=True)
        df_departamentos.columns = ['corresponde_a', 'texto_departamento', 'url_departamento']
        df_departamentos['url_texto_departamento'] = df_departamentos['url_departamento'].str.split('/', expand=True)[3].str.lower()
        return df_departamentos

    def get_entity_categorias(self, df_main_entities):
        df_categorias = df_main_entities[df_main_entities['correspondeA']=='CATEGORIA'].reset_index(drop=True)
        df_categorias.columns = ['corresponde_a', 'texto_categorias', 'url_categorias']
        df_categorias['url_texto_departamento'] = df_categorias['url_categorias'].str.split('/', expand=True)[3].str.lower()
        df_categorias['url_texto_categorias'] = df_categorias['url_categorias'].str.split('/', expand=True)[4].str.lower()
        return df_categorias

    def get_entity_subcategorias(self, df_main_entities):
        df_subcategorias = df_main_entities[df_main_entities['correspondeA']=='SUBCATEGORIA'].reset_index(drop=True)
        df_subcategorias.columns = ['corresponde_a', 'texto_subcategorias', 'url_subcategorias']
        df_subcategorias['url_texto_departamento'] = df_subcategorias['url_subcategorias'].str.split('/', expand=True)[3].str.lower()
        df_subcategorias['url_texto_categorias'] = df_subcategorias['url_subcategorias'].str.split('/', expand=True)[4].str.lower()
        df_subcategorias['url_texto_subcategorias'] = df_subcategorias['url_subcategorias'].str.split('/', expand=True)[5].str.lower()
        return df_subcategorias

    def run(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument('--blink-settings=imagesEnabled=false')

        driver = webdriver.Chrome(options=options)

        logging.info(f"Getting main entities from website")
        df_main_entities = self.get_main_entities(url=self.url_main, 
                                                  driver=driver, 
                                                  time_wait=self.time_wait)

        driver.quit()

        logging.info(f"Cleaning data")
        df_marcas = self.get_entity_marcas(df_main_entities)
        df_productos = self.get_entity_productos(df_main_entities)
        df_departamentos = self.get_entity_departamentos(df_main_entities)
        df_categorias = self.get_entity_categorias(df_main_entities)
        df_subcategorias = self.get_entity_categorias(df_main_entities)

        del df_main_entities

        logging.info(f"Saving data")
        df_marcas.to_csv('./data/entities/marcas.csv', index=False, encoding='utf-8')
        df_productos.to_csv('./data/entities/productos.csv', index=False, encoding='utf-8')
        df_departamentos.to_csv('./data/entities/departamentos.csv', index=False, encoding='utf-8')
        df_categorias.to_csv('./data/entities/categorias.csv', index=False, encoding='utf-8')
        df_subcategorias.to_csv('./data/entities/subcategorias.csv', index=False, encoding='utf-8')

        logging.info(f"Success")

def main():
    """Run the project's main ETL process"""
    
    etl = DailyScraperEntities(
        url_main=URL_MAIN, 
        environment=ENVIRONMENT,
        time_wait=TIME_WAIT)

    etl.run()


if __name__ == '__main__':

    URL_MAIN = 'https://www.vea.com.ar/'
    ENVIRONMENT = 'test'
    TIME_WAIT = 10
    
    main()
