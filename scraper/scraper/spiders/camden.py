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
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium_stealth import stealth
#from inline_requests import inline_requests
from scraper.items import GenericcouncilItem
from scraper.items import DocumentsItem
from scraper.items import GeneralItem
from scraper.items import CamdenItems
from scraper.scrapy_selenium2.http import SeleniumRequest, SeleniumRequestUpdatePageSourceAsBody
from scraper.HtmlRequestByPassMiddleware import RateLimiterHandler

class CamdenSpider(scrapy.Spider):
    name = "camden"
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
    #start_date      = '01/01/2025'
    #end_date        = '03/01/2025'

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
                 rate_limit=None,range=None,*args,**kwargs):
        super(CamdenSpider,self).__init__(*args,**kwargs)
        self.rate_period=delay_sec
        self.rate_limit=rate_limit


        if range!=None:
            self.range=range
        if delay_sec!=None:
            self.rate_period=delay_sec
            self.rate_limit=1
        if start_url:
            self.log('### Command line URL: %s ###' % start_url)
            self.start_url=start_url
        else:
            self.start_url='https://planningrecords.camden.gov.uk/NECSWS/PlanningExplorer/GeneralSearch.aspx'
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

        '''
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
        '''
        
    
    def start_requests(self):
      
        yield SeleniumRequest(url=self.start_url,callback=self.doSearch,implicitly_wait=120,time_sleep_millisec=6000)
            #url=https://publicaccess.newark-sherwooddc.gov.uk/online-applications/search.do?action=advanced

    def doSearch(self,response):
        self.log('### Scraping: doSearch ###')
        self.log(response.url)
        #url='https://publicaccess.newark-sherwooddc.gov.uk/online-applications/search.do?action=advanced'
        #result_url = self.result_url % self.start_url
        #result_url='https://publicaccess.newark-sherwooddc.gov.uk/online-applications/advancedSearchResults.do?action=firstPage'
        #self.log('Calling %s' % result_url)
        
        manual_request = False

        if self.range=='7':
            # Get today's date
            today = datetime.today()
            # Get the date 7 days ago
            seven_days_ago = today - timedelta(days=7)
            # Format it as day/month/year
            formatted_date = seven_days_ago.strftime("%d/%m/%Y")
            self.start_date      = formatted_date 
            self.end_date        = datetime.today().strftime("%d/%m/%Y")
            print(self.start_date)
            print(self.end_date)
        elif self.range=='14':
            # Get today's date
            today = datetime.today()
            # Get the date 14 days ago
            seven_days_ago = today - timedelta(days=14)
            # Format it as day/month/year
            formatted_date = seven_days_ago.strftime("%d/%m/%Y")
            self.start_date      = formatted_date 
            self.end_date        = datetime.today().strftime("%d/%m/%Y")
            print(self.start_date)
            print(self.end_date)


        if self.site=="uk" and manual_request==False:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.driver.find_element(By.XPATH,'//option[@value="DATE_DECISION"]').click()
            start_date_field=self.driver.find_element(By.XPATH,'//input[@name="dateStart"]')
            start_date_field.send_keys(self.start_date)
            time.sleep(5)
            end_date_field=self.driver.find_element(By.XPATH,'//input[@name="dateEnd"]')

            end_date_field.send_keys(self.end_date)
            time.sleep(5)
            self.driver.find_element(By.XPATH,'//input[@type="submit"]').click()
            time.sleep(15)
            

            yield SeleniumRequestUpdatePageSourceAsBody(url=self.driver.current_url,
                                                    page_source_as_html=self.driver.page_source,
                                                    callback=self.parse,
                                                    dont_filter=True #Prevent duplicate filtering if dublicate url so allow
                                                    )
               
            
    def parse(self,response):
        base_url = "https://planningrecords.camden.gov.uk/NECSWS/PlanningExplorer/Generic/"
        
        table=response.xpath('//table/tbody/tr')[1:]
        for link in table:
            item_link=link.xpath('./td/a/@href').get()
            new_url=base_url+item_link

            yield SeleniumRequest(url=new_url,callback=self.scrapemainpage,implicitly_wait=120,time_sleep_millisec=6000)

        next_page=response.xpath("//a[@class='noborder' and img[@alt='Go to next page']]")
        if next_page:
            rel_next_page_url=response.xpath("//a[@class='noborder' and img[@alt='Go to next page']]/@href").get()
            next_page_url=base_url+rel_next_page_url
            yield SeleniumRequest(url=next_page_url,callback=self.parse,implicitly_wait=120,time_sleep_millisec=6000)
        else:
            print('All pages scraped')
        
    def scrapemainpage(self,response):

        appItem=CamdenItems()

        appItem['decision']=response.xpath("//div/span[text()='Decision']/following-sibling::text()[1]").get()
        appItem['appno']=response.xpath("//div/span[text()='Application Number']/following-sibling::text()[1]").get()
        appItem['siteAdd']=response.xpath("//div/span[text()='Site Address']/following-sibling::text()[1]").get()
        appItem['appType']=response.xpath("//div/span[text()='Application Type']/following-sibling::text()[1]").get()
        appItem['proposal']=response.xpath("//div/span[text()='Proposal']/following-sibling::text()[1]").get()
        appItem['applicant']=response.xpath("//div/span[text()='Applicant']/following-sibling::text()[1]").get()


        yield appItem