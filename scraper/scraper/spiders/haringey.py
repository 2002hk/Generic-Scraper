import scrapy
import scrapy, logging, re
from scrapy.utils.log import configure_logging
from scrapy.http.cookies import CookieJar
from scrapy.http import FormRequest
from scrapy.shell import inspect_response
from scrapy.utils.response import open_in_browser
from urllib.parse import urlparse, parse_qs
from scraper.items import GenericcouncilItem
from scraper.HtmlRequestByPassMiddleware import HtmlRequestByPass,HtmlRequestRest
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

import undetected_chromedriver as uc
from selenium_stealth import stealth
#from inline_requests import inline_requests
from scraper.items import GenericcouncilItem
from scraper.items import DocumentsItem
from scraper.items import GeneralItem
from scraper.items import HaringeyItems
from scraper.scrapy_selenium2.http import SeleniumRequest, SeleniumRequestUpdatePageSourceAsBody
from scraper.HtmlRequestByPassMiddleware import RateLimiterHandler


class HaringeySpider(scrapy.Spider):
    name = "haringey"
    #allowed_domains = ["random.com"]

    site=None
    is_selenium_site=True
    selenium_allow_site=["uk"]
    run_headless="NO"
    driver : uc.Chrome = None
    rateLimit:RateLimiterHandler=RateLimiterHandler(enable=False)
    rate_period = None #sec
    rate_limit = None #max req in sec

    start_urls      = ['%s/online-applications/search.do?action=advanced']
    summmary_url    = '%s/online-applications/applicationDetails.do?activeTab=summary&keyVal=%s'
    details_url     = '%s/online-applications/applicationDetails.do?activeTab=details&keyVal=%s'
    contacts_url    = '%s/online-applications/applicationDetails.do?activeTab=contacts&keyVal=%s'
    documents_url   = '%s/online-applications/applicationDetails.do?activeTab=documents&keyVal=%s'
    domain_url      = '%s%s'
    next_search_url = '%s/online-applications/pagedSearchResults.do?action=page&searchCriteria.page=%s'
    result_url      = '%s/online-applications/advancedSearchResults.do?action=firstPage'

    start_date      = '01/01/2025' ## month/date/year
    end_date        = '01/20/2025'

    fetch_method    = 'POST'

    custom_settings = {
        # specifies exported fields and order
        # 'FEED_EXPORT_FIELDS': ["key","applicationType", "address", "applicantName", "applicantAddress", 
        #             "parish", "ward", "agentName", "agentEmail", "agentPhone", "agentMobile", "agentFax", "agentAddress","agentCompanyName","decisionDate","proposal", "documentsLink", "applicationForm", "decisionNotice", "psSearchDecision", "psSurname", "psPostCode", "psResult1", 
        #             "psResultCount1", "psResult2", "psResultCount2", "psSearchUrl1", 
        #             "psSearchUrl2"],

        'FEED_EXPORT_FIELDS': ["key","applicationType","address","applicantName","proposal","applicantAddress",
                               "agentName","agentEmail","agentPhone","agentMobile","agentAddress",
                               "documentsLink"

                                #capture but not saving as per 
                               #"psSearchDecision","psSurname","psPostCode","psResult1","psResultCount1",
                                #"psResult2","psResultCount2","psSearchUrl1","psSearchUrl2"
                            ],

        #driver config
        #"SELENIUM_ENABLE": False,
        "SELENIUM_DRIVER_NAME":"chrome",
        "SELENIUM_DRIVER_ARGUMENTS" : [ ],
        #"SELENIUM_WEBDRIVER_CHROME_OPTIONS": None,
        #"SELENIUM_DRIVER_EXECUTABLE_PATH": None,
        # "SELENIUM_USE_DRIVER_MANUALLY_CREATED":None,
        # "SELENIUM_CALLABLE_DRIVER_CREATED":None,

        #Request Default props
        "SELENIUM_DEFAULT_REQUEST_TIME_SLEEP_MILLI_SEC": None,
        "SELENIUM_DEFAULT_REQUEST_IMPLICITLY_WAIT": None,
        "SELENIUM_DEFAULT_REQUEST_PAGE_SOURCE_AS_BODY": None,
        "SELENIUM_DEFAULT_REQUEST_WAIT_TIME": None,
        "SELENIUM_DEFAULT_REQUEST_WAIT_UNTIL": None,
        "SELENIUM_DEFAULT_REQUEST_SCREENSHOT": None,
        "SELENIUM_DEFAULT_REQUEST_SCRIPT": None,
        "SELENIUM_DEFAULT_REQUEST_SCRIPT_AFTER_TIME_SLEEP_MILLI_SEC": None
    }
    
    configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename='log.txt',
        format='%(levelname)s: %(message)s',
        level=logging.INFO
    )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        #creating the spider instance
        spider = super().from_crawler(crawler, *args, **kwargs)
        if "site" in kwargs:
            site = kwargs["site"]
            
            #update
            spider.is_selenium_site = site in spider.selenium_allow_site

            if site in spider.selenium_allow_site:
                spider.log('### Selenium driver for : %s ###' % site)

                #if site == "EppingForest":
                #    spider.run_headless = 'YES'

                # spider.settings.set("CONCURRENT_REQUESTS", 1)
                # spider.settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", 1)
                # spider.settings.set("CONCURRENT_REQUESTS_PER_IP", 1)
                # spider.settings.set("REACTOR_THREADPOOL_MAXSIZE", 1)
                # spider.settings.set("AUTOTHROTTLE_ENABLED", False)
                spider.settings.set("URLLENGTH_LIMIT", 5000)

                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Safari/537.36"
                options = None

                if spider.run_headless == 'NO':
                    spider.log('### Selenium driver - Running Selenium with head')

                    options = webdriver.ChromeOptions()
                    #options = uc.ChromeOptions()

                    # options.add_argument('--headless=new')
                    # options.add_argument('--disable-gpu')
                    # options.add_argument("--remote-debugging-port=9222")
                    # options.headless = True

                    options.add_argument('--ignore-certificate-errors')
                    options.add_argument('--ignore-ssl-errors')
                    options.add_argument('--start-maximized')
                    options.add_argument('--disable-notifications')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-popup-blocking')
                    options.add_argument("--user-agent={}".format(user_agent))
                    #options.add_argument('--blink-settings=imagesEnabled=false')

                    options.add_argument('--disable-infobars')

                    #load fast
                    options.add_argument('--disable-extensions')  # Disable extensions
                    options.add_argument('--disable-dev-shm-usage')

                else:
                    options = webdriver.ChromeOptions()
                    #options = uc.ChromeOptions()

                    options.add_argument('--headless=new')
                    options.add_argument('--disable-gpu')

                    # chrome://inspect/#devices for inspect
                    # options.add_argument('--remote-debugging-port=9222')  # Open DevTools port
                    # options.add_argument('--remote-allow-origins=*')  # Allow all remote origins
                    # options.debugger_address = "127.0.0.1:9222"

                    options.headless = True

                    options.add_argument('--remote-allow-origins=*')  # Allow all remote origins

                    options.add_argument('--ignore-certificate-errors')
                    options.add_argument('--ignore-ssl-errors')
                    options.add_argument('--start-maximized')
                    options.add_argument('--disable-notifications')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-popup-blocking')
                    options.add_argument("--user-agent={}".format(user_agent))
                    options.add_argument('--disable-infobars')
                    #options.add_argument('--blink-settings=imagesEnabled=false')

                    #load fast
                    #options.add_argument('--disable-extensions')  # Disable extensions
                    options.add_argument('--disable-dev-shm-usage')

                #create manually driver
                chrome_driver_path = "C:/Users/hrutu/Desktop/GenericScraper/scraper/chromedriver.exe"

                options = webdriver.ChromeOptions()
                service = Service(chrome_driver_path)  # Manually specify the path
                #driver = webdriver.Chrome(service=service, options=options)
                driver = uc.Chrome(options=options,service=service)

                stealth(driver,
                        languages=["en-US", "en"],
                        vendor="Google Inc.",
                        platform="Win32",
                        webgl_vendor="Intel Inc.",
                        renderer="Intel Iris OpenGL Engine",
                        fix_hairline=True,
                    )


                #pass options to driver 
                spider.settings.set("SELENIUM_USE_DRIVER_MANUALLY_CREATED", driver )
                spider.settings.set("SELENIUM_WEBDRIVER_CHROME_OPTIONS", options )
                spider.settings.set("SELENIUM_ENABLE", True)
                spider.settings.set("SELENIUM_CALLABLE_DRIVER_CREATED", spider.driver_created)


                #update rate limit if not set default 
                if spider.rate_period == None or spider.rate_limit == None:
                    spider.rate_period = 5 #10
                    spider.rate_limit = 1

        #rate limit class init 
        if spider.rate_period != None and spider.rate_limit != None:
            spider.rateLimit = RateLimiterHandler(True ,max_calls=spider.rate_limit,period=spider.rate_period,spider=spider)

        spider.log(f"Rate limit period: {spider.rate_period} sec max_call {spider.rate_limit} ")

        return spider

    def driver_created(self):
        # Inject JavaScript using CDP (Chrome DevTools Protocol)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            }
        )

    #each req after sec of delay based on rate limit
    def default_delay(self):
        #self.rate_period
        self.rateLimit.wait_until_next_request()
        pass
    def text_replace(self,text,search,replace):
        if text == None:
            return text
        return text.replace(search,replace)

    def text_strip(self,text):
        if text == None:
            return text
        return text.strip()


    def __init__(self,start_date=None,end_date=None,start_url=None,custom_set=None,fetch_method=None,fetch_decisions=None,delay_sec=None,
                 rate_limit=None,*args,**kwargs):
        super(HaringeySpider,self).__init__(*args,**kwargs)
        self.rate_period=delay_sec
        self.rate_limit=rate_limit

        if delay_sec!=None:
            self.rate_period=delay_sec
            self.rate_limit=1
        if start_url:
            self.log('### Command line URL: %s ###' % start_url)
            self.start_url=start_url
        else:
            self.start_url='https://publicregister.haringey.gov.uk/pr/s/register-view?c__q=eyJyZWdpc3RlciI6IkFyY3VzX0JFX1B1YmxpY19SZWdpc3RlciIsInJlcXVlc3RzIjpbeyJyZWdpc3Rlck5hbWUiOiJBcmN1c19CRV9QdWJsaWNfUmVnaXN0ZXIiLCJzZWFyY2hUeXBlIjoiYWR2YW5jZWQiLCJzZWFyY2hOYW1lIjoiUGxhbm5pbmdfQXBwbGljYXRpb25zIiwiYWR2YW5jZWRTZWFyY2hOYW1lIjoiUEFfQURWX0FsbCIsInNlYXJjaEZpbHRlcnMiOlt7ImZpZWxkTmFtZSI6Ik5hbWUiLCJmaWVsZFZhbHVlIjoiIiwiZmllbGREZXZlbG9wZXJOYW1lIjoiUEFfQURWX0FwcGxpY2F0aW9uUmVmZXJlbmNlIn0seyJmaWVsZE5hbWUiOiJIaWRkZW5fUFJfU2l0ZV9hZGRyZXNzX19jIiwiZmllbGRWYWx1ZSI6IiIsImZpZWxkRGV2ZWxvcGVyTmFtZSI6IlBBX0FEVl9TaXRlQWRkcmVzcyJ9LHsiZmllbGROYW1lIjoiSGlkZGVuX1Bvc3Rjb2RlX1BMX19jIiwiZmllbGRWYWx1ZSI6IiIsImZpZWxkRGV2ZWxvcGVyTmFtZSI6IlBvc3Rjb2RlX1BMIn0seyJmaWVsZE5hbWUiOiJhcmN1c2J1aWx0ZW52X19Qcm9wb3NhbF9fYyIsImZpZWxkVmFsdWUiOiIiLCJmaWVsZERldmVsb3Blck5hbWUiOiJQQV9BRFZfUHJvcG9zYWwifSx7ImZpZWxkTmFtZSI6ImFyY3VzYnVpbHRlbnZfX1R5cGVfX2MiLCJmaWVsZFZhbHVlIjoiIiwiZmllbGREZXZlbG9wZXJOYW1lIjoiUEFfQURWX0FwcGxpY2F0aW9uVHlwZSJ9LHsiZmllbGROYW1lIjoiYXJjdXNidWlsdGVudl9fV2FyZHNfX2MiLCJmaWVsZFZhbHVlIjoiIiwiZmllbGREZXZlbG9wZXJOYW1lIjoiUEFfQURWX1dhcmROYW1lIn0seyJmaWVsZE5hbWUiOiJhcmN1c2J1aWx0ZW52X19WYWxpZF9EYXRlX19jIiwiZmllbGRWYWx1ZSI6IiIsImZpZWxkRGV2ZWxvcGVyTmFtZSI6IlBBX0FEVl9EYXRlVmFsaWRhdGVkRnJvbSJ9LHsiZmllbGROYW1lIjoiYXJjdXNidWlsdGVudl9fVmFsaWRfRGF0ZV9fYyIsImZpZWxkVmFsdWUiOiIiLCJmaWVsZERldmVsb3Blck5hbWUiOiJQQV9BRFZfRGF0ZVZhbGlkYXRlZFRvIn0seyJmaWVsZE5hbWUiOiJhcmN1c2J1aWx0ZW52X19EZWNpc2lvbl9Ob3RpY2VfU2VudF9EYXRlX01hbnVhbF9fYyIsImZpZWxkVmFsdWUiOm51bGwsImZpZWxkRGV2ZWxvcGVyTmFtZSI6IlBBX0FEVl9EZWNpc2lvbkRhdGVGcm9tIn0seyJmaWVsZE5hbWUiOiJhcmN1c2J1aWx0ZW52X19EZWNpc2lvbl9Ob3RpY2VfU2VudF9EYXRlX01hbnVhbF9fYyIsImZpZWxkVmFsdWUiOm51bGwsImZpZWxkRGV2ZWxvcGVyTmFtZSI6IlBBX0FEVl9EZWNpc2lvbkRhdGVUbyJ9LHsiZmllbGROYW1lIjoiYXJjdXNidWlsdGVudl9fRXh0ZXJuYWxfSWRfX2MiLCJmaWVsZFZhbHVlIjoiIiwiZmllbGREZXZlbG9wZXJOYW1lIjoiUEFfQURWX1BsYW5uaW5nUG9ydGFsUmVmZXJlbmNlTnVtYmVyIn1dfV19&c__r=Arcus_BE_Public_Register'
            self.log('### Using default URL: %s ###' % self.start_url)
        if custom_set:
            self.log('### Command line custom set: %s ###' % custom_set)
            self.custom_set = custom_set
        else:
            self.custom_set = '1'
            self.log('### Using default set: %s ###' % self.start_url)
        if fetch_method:
            self.fetch_method = fetch_method
            self.log('### Fetch method changed to: %s ###' % self.fetch_method)
        if fetch_decisions:
            self.fetch_decisions = fetch_decisions
            self.log('### Fetch decisions changed to: %s ###' % self.fetch_decisions)
        else:
            self.fetch_decisions=None
        if start_date:
            self.log('### Command start date: %s ###' % start_date)
            self.start_date = start_date
        else:
            self.log('### Command start date: %s ###' % self.start_date)
        
        if end_date:
            self.log('### Command end date: %s ###' % end_date)
            self.end_date = end_date
        else:
            self.log('### Command end date: %s ###' % self.end_date)   
    
    def start_requests(self):
      
        yield SeleniumRequest(url=self.start_url,callback=self.doSearch,implicitly_wait=120,time_sleep_millisec=6000)
            #url=https://publicaccess.newark-sherwooddc.gov.uk/online-applications/search.do?action=advanced
    def doSearch(self,response):
        # Wait until the dropdown is clickable and click to open
        '''
        dropdown = WebDriverWait(self.driver, 10).until(
        EC.element_to_be_clickable((By.ID, "combobox-button-8"))  # Replace with correct ID
        )
        dropdown.click()
        # Wait for options to be visible
        options_list = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//span[@title="Planning Applications"]'))
        )

        # Hover over "Planning Applications" and click
        action = ActionChains(self.driver)
        action.move_to_element(options_list[0]).click().perform()
        
        '''
        
        search_buttons=self.driver.find_elements(By.XPATH,'//button[@class="pr-buttonLink slds-button"]')
        search_buttons[1].click()
        #self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        dateinputs=self.driver.find_elements(By.XPATH,'//input[@class="slds-input"]')
        dateinputs[5].send_keys(self.start_date)
        
        time.sleep(5)
        dateinputs[6].send_keys(self.end_date)
        time.sleep(5)
        self.driver.find_element(By.XPATH,'//button[@class="slds-button slds-button_brand"]').click()
        time.sleep(10)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)
        #yield SeleniumRequest(url=self.driver.current_url, callback=self.parse, dont_filter=True, time_sleep_millisec=500)
 
        
        while True:
            appItem=HaringeyItems()
            containers=self.driver.find_elements(By.XPATH,'//div[@class="slds-form slds-box"]')
            print('*********************** length containers',len(containers))
            print('***************************',containers)
            for container in containers:
                container_elements=container.find_elements(By.XPATH,'.//div[@class="slds-form-element__control"]')
                print('********************container_elements',container_elements)

                appItem['appref']=container_elements[0].find_element(By.XPATH,'./lightning-formatted-url/a').text
                appItem['proposal']=container_elements[1].find_element(By.XPATH,'./lightning-formatted-text').text
                appItem['appstatus']=container_elements[2].find_element(By.XPATH,'./lightning-formatted-text').text
                appItem['siteadd']=container_elements[3].find_element(By.XPATH,'./lightning-formatted-text').text
                appItem['datevalid']=container_elements[4].find_element(By.XPATH,'./lightning-formatted-text').text
                appItem['decision']=container_elements[5].find_element(By.XPATH,'./lightning-formatted-text').text
                appItem['decisionNotice']=container_elements[6].find_element(By.XPATH,'./lightning-formatted-text').text

                yield appItem
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                self.driver.find_element(By.XPATH,'//a[@class="pr-pagination__link" and text()="Next"]').click()
            except Exception as e:
                print(f'****Exception occured {e}*****')
                print('all pages scraped')
                break
        
        
   
        