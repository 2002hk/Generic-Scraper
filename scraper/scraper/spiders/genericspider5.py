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
from scrapy.utils.defer import parallel_async
from twisted.internet import defer
import undetected_chromedriver as uc
from selenium_stealth import stealth
#from inline_requests import inline_requests
from scraper.items import GenericcouncilItem
from scraper.items import DocumentsItem
from scraper.items import GeneralItem
from scraper.scrapy_selenium2.http import SeleniumRequest, SeleniumRequestUpdatePageSourceAsBody
from scraper.HtmlRequestByPassMiddleware import RateLimiterHandler
from datetime import datetime, timedelta
class Genericspider5Spider(scrapy.Spider):
    name = "genericspider5"
    #allowed_domains = ["random.com"]

    site=None
    is_selenium_site=False
    selenium_allow_site=["uk"]
    run_headless="YES"
    driver : uc.Chrome = None
    rateLimit:RateLimiterHandler=RateLimiterHandler(enable=False)
    rate_period = None #sec
    rate_limit = None #max req in sec
    range=None
    start_urls      = ['%s/online-applications/search.do?action=advanced']
    summmary_url    = '%s/online-applications/applicationDetails.do?activeTab=summary&keyVal=%s'
    details_url     = '%s/online-applications/applicationDetails.do?activeTab=details&keyVal=%s'
    contacts_url    = '%s/online-applications/applicationDetails.do?activeTab=contacts&keyVal=%s'
    documents_url   = '%s/online-applications/applicationDetails.do?activeTab=documents&keyVal=%s'
    domain_url      = '%s%s'
    next_search_url = '%s/online-applications/pagedSearchResults.do?action=page&searchCriteria.page=%s'
    result_url      = '%s/online-applications/advancedSearchResults.do?action=firstPage'

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
                    options.add_argument('--disable-popup-blocking')
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
                    options.add_argument('--disable-popup-blocking')
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

                #options = webdriver.ChromeOptions()
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
                    spider.rate_period = 10 #10
                    spider.rate_limit = 1

        #rate limit class init 
        if spider.rate_period != None and spider.rate_limit != None:
            spider.rateLimit = RateLimiterHandler(True,
            max_calls=int(spider.rate_limit),  # Convert rate_limit to int
            period=int(spider.rate_period),    # Convert rate_period to int
            spider=spider)

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
                 rate_limit=None,site_to_scrape=None,range=None,*args,**kwargs):
        super(Genericspider5Spider,self).__init__(*args,**kwargs)
        self.rate_period=delay_sec
        self.rate_limit=rate_limit


        if site_to_scrape!=None:
            self.site_to_scrape=site_to_scrape
        if range!=None:
            self.range=range
        if delay_sec!=None:
            self.rate_period=delay_sec
            self.rate_limit=1
        if start_url:
            self.log('### Command line URL: %s ###' % start_url)
            self.start_url=start_url
        else:
            self.start_url='https://planning.lewisham.gov.uk'
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
            #self.log('### Command start date: %s ###' % start_date)
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
        for i, url in enumerate(self.start_urls):
            url=url%self.start_url
            yield scrapy.Request(url,callback=self.doSearch)


    def doSearch(self,response):
        self.log('### Scraping: doSearch ###')
        self.log(response.url)
        #url='https://publicaccess.newark-sherwooddc.gov.uk/online-applications/search.do?action=advanced'
        result_url = self.result_url % self.start_url
        #result_url='https://publicaccess.newark-sherwooddc.gov.uk/online-applications/advancedSearchResults.do?action=firstPage'
        self.log('Calling %s' % result_url)

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

        form_no_0_sites=['barnet','enfield','greenwich','lambeth','lewisham','newham','southwark']
        form_no_1_sites=['brent','westminster']
        manual_request = False
        if self.fetch_decisions=='yes':
            if self.site_to_scrape in form_no_0_sites:
                yield scrapy.FormRequest.from_response(response=response,
                                                   formdata={
                                                            "date(applicationDecisionStart)": self.start_date,
                                                            "date(applicationDecisionEnd)":self.end_date,
                                                            "searchType": "Application",
                                                                },
                                                    formnumber=0,
                                                    callback=self.parse,
                                                    method=self.fetch_method
                                                   
                                                   )
            if self.site_to_scrape in form_no_1_sites:
                 yield scrapy.FormRequest.from_response(response=response,
                                                   formdata={
                                                            "date(applicationDecisionStart)": self.start_date,
                                                            "date(applicationDecisionEnd)":self.end_date,
                                                            "searchType": "Application",
                                                                },
                                                    formnumber=1,
                                                    callback=self.parse,
                                                    method=self.fetch_method
                                                   
                                                   )
       
        else:
            yield scrapy.FormRequest.from_response(response=response,
                                                   formdata={
                                                        "date(applicationValidatedStart)": self.start_date,
                                                        "date(applicationValidatedEnd)":self.end_date,
                                                        'searchType':'Application',
                                                        'caseAddressType':'Application',
                                                        'submit':'Search',
                                                            },
                                                    formid='advanceSearchForm',
                                                    callback=self.parse,
                                                    method=self.fetch_method
                                                   
                                                   )

        self.is_selenium_site=False
        if self.site=="uk" and manual_request==False and self.is_selenium_site==True:
            tabs=self.driver.find_elements(By.XPATH,'//ul[@class="tabs"]/li/a')
            tabs[1].click()
            if response.url=='https://publicaccess.barnet.gov.uk/online-applications/search.do?action=advanced':
                self.driver.find_element(By.XPATH,'//option[@value="FUL"]').click()
                time.sleep(3)
            start_date_field=self.driver.find_element(By.XPATH,'//input[@name="date(applicationDecisionStart)"]')
            end_date_field=self.driver.find_element(By.XPATH,'//input[@name="date(applicationDecisionEnd)"]')

            start_date_field.send_keys(self.start_date)
            end_date_field.send_keys(self.end_date)
            self.driver.find_element(By.XPATH,'//input[@type="submit" and @value="Search"]').click()
            time.sleep(10)
            yield SeleniumRequestUpdatePageSourceAsBody(url=self.driver.current_url,
                                                    page_source_as_html=self.driver.page_source,
                                                    callback=self.parse,
                                                    dont_filter=True #Prevent duplicate filtering if dublicate url so allow
                                                    )


    def parse(self,response):
        self.log('### Scraping: parse ###')
        self.log(response.url)
        self.default_delay()
        time.sleep(5)  # Wait for the page to fully load
        container_link=response.xpath('//ul[@id="searchresults"]//a[1]/@href').getall()
        print('*******************len************', len(container_link))
        time.sleep(10) 
        next_url=response.xpath('//a[@class="next"]/@href').get()
        if next_url:
                parsed_url = urlparse(next_url)
                par = parse_qs(parsed_url.query)
                appKey = par['searchCriteria.page'][0]
                self.log(f'Next page: {appKey}')
                next_url = self.next_search_url % (self.start_url, appKey)

        for link in container_link:
            parsed_url = urlparse(link)
            par = parse_qs(parsed_url.query)
            appKey = par['keyVal'][0]
            self.log(appKey)
            self.requests=[]
            url=self.summmary_url % (self.start_url, appKey)
            self.default_delay()
            yield scrapy.Request(url=url, callback=self.scrapeSummary, dont_filter=True,meta={'appKey':appKey})
            doc_url=self.documents_url % (self.start_url, appKey)
            self.logger.info(f"Yielding document request: {doc_url}")
            yield scrapy.Request(url=doc_url, callback=self.scrapeDocuments, dont_filter=True)
            
 
        try:
            self.default_delay()
            yield scrapy.Request(next_url, callback=self.parse, dont_filter=True)
        except Exception as e:
            self.log(f"Pagination error: {e}")
    
        
                
    def scrapeSummary(self,response):
        self.log('#### SCRAPING: SUMMARY ####')
        appItem = GenericcouncilItem()
        #appItem = response.meta['appitem']
        appItem['key'] = response.meta['appKey']
        link = response.request.url
            #self.log(link)
        parsed_url = urlparse(link)
        par = parse_qs(parsed_url.query)
            #par = urlparse(link).params
        appKey = par['keyVal'][0]
        appItem['key']=appKey

        for row in response.xpath('//tr'):
            header=row.xpath('.//th/text()').get()
            header=self.text_replace(header,'\n','')
            header=self.text_strip(header)

            if header=='Address':
                value = row.xpath('.//td/text()').extract_first()
                value = self.text_replace(value,'\n','')
                value = self.text_strip(value)
                appItem['address'] = value
           
            if header=='Proposal':
                value = row.xpath('.//td').extract_first()
                value = self.text_replace(value,'\n','')
                value = self.text_replace(value,'<br>',' ')
                value = self.text_replace(value,'<td>','')
                value = self.text_replace(value,'</td>','')
                value = self.text_replace(value,'&amp;','')
                value = self.text_replace(value,'"',"'")
                value = self.text_replace(value,';',",")
                value = self.text_strip(value)
                appItem['proposal'] = value

        
        url=self.details_url % (self.start_url, appKey)
        self.default_delay()
    
        yield scrapy.Request(url=url, callback=self.scrapeDetails, dont_filter=True,meta={'item':appItem})
        
        
    def scrapeDetails(self,response):
        
        appItem = response.meta['item']
        for row in response.xpath('//tr'):
            header = row.xpath('.//th/text()').extract_first()
            header = self.text_replace(header,'\n','')
            header = self.text_strip(header)
            if header=='Application Type':
                value = row.xpath('.//td/text()').extract_first()
                if value is not None:
                    value = self.text_replace(value,'\n','')
                    value = self.text_strip(value)
                    appItem['applicationType'] = value
           
            if header=='Applicant Name':
                value = row.xpath('.//td/text()').extract_first()
                if value is not None:
                    value = self.text_replace(value,'\n','')
                    value = self.text_strip(value)
                    appItem['applicantName'] = value  
            if header=='Applicant Address':
                value = row.xpath('.//td/text()').extract_first()
                if value is not None:
                    value = self.text_replace(value,'\n','')
                    value = self.text_strip(value)
                    appItem['applicantAddress'] = value  
            if header=='Agent Name':
                value = row.xpath('.//td/text()').extract_first()
                if value is not None:
                    value = self.text_replace(value,'\n','')
                    value = self.text_strip(value)
                    appItem['agentName'] = value
            if header=='Agent Address':
                value = row.xpath('.//td/text()').extract_first()
                if value is not None:
                    value = self.text_replace(value,'\n','')
                    value = self.text_strip(value)
                    appItem['agentAddress'] = value
                    print("aagentAddress",value)
        
        
        url=self.contacts_url % (self.start_url, response.meta['item']['key'])
        
        self.default_delay()
       
        yield scrapy.Request(url=url, callback=self.scrapeContacts, dont_filter=True,meta={'item': appItem})

        
    def scrapeContacts(self,response):
        
        appItem = response.meta['item']
        agent_name = response.xpath('//div[@class="agents"]/p/text()').extract_first()
        
        if agent_name is not None:
            appItem['agentName'] = agent_name
             
        table = response.xpath('//table[@class="agents"]')
        for row in table.xpath('.//tr'):
            header = row.xpath('.//th/text()').extract_first()
            header = self.text_replace(header,'\n','')
            header = self.text_replace(header,'  ',' ')
            header = self.text_replace(header,'  ',' ')
            header = self.text_strip(header)
            
            if header.upper()=='E-mail'.upper() or header.upper()=='Personal Email'.upper() \
                or header.upper() =='Email'.upper():
                value = row.xpath('.//td/text()').extract_first()
                value = self.text_replace(value,'\n','')
                value = self.text_strip(value)
                appItem['agentEmail'] = value  
                print("agentEmail : ",value) 
            if header.upper()=='Phone'.upper() or header.upper()=='Home Phone Number'.upper() \
                    or header.upper()=='Personal Phone'.upper() or header.upper()=='Phone contact number'.upper() \
                    or header.upper()=='Telephone number'.upper():
                value = row.xpath('.//td/text()').extract_first()
                value = self.text_replace(value,'\n','')
                value = self.text_strip(value)
                appItem['agentPhone'] = value
            if header.upper()=='Mobile'.upper() or header.upper()=='Mobile Phone'.upper() \
                            or header.upper() == 'Personal Mobile'.upper():
                value = row.xpath('.//td/text()').extract_first()
                value = self.text_replace(value,'\n','')
                value = self.text_strip(value)
                appItem['agentMobile'] = value
            
        self.default_delay()
        yield appItem

    def scrapeDocuments(self,response):
       
        
        with open('C:/Users/hrutu/Desktop/GenericScraper/doc_response.html','wb') as f:
            f.write(response.body)
        self.log("Saved file: doc_response.html")

        self.logger.info(f"******************documnets getting scraped***************")
        self.log(response.url)
        rows = response.xpath('//table[@id="Documents"]//tr')[1:] # Skip the first row (header)# Get all rows in the table
        with open('C:/Users/hrutu/Desktop/GenericScraper/doc_response2.html','wb') as f:
            f.write(response.body)
        print('*************************doc rows len***************************',len(rows))
        for row in rows:
            appItem2 = DocumentsItem()
            link = response.request.url
            #self.log(link)
            parsed_url = urlparse(link)
            par = parse_qs(parsed_url.query)
            #par = urlparse(link).params
            appKey = par['keyVal'][0]
            
            cols = row.xpath('./td')  # Get all columns in a single row
            print('********************doc col len********************',len(cols))
            if len(cols) == 5:  # If the table has 5 columns
                appItem2['datePub'] = cols[1].xpath('./text()').get()
                appItem2['doctype'] = cols[2].xpath('./text()').get()
                appItem2['desc'] = cols[3].xpath('./text()').get()
                appItem2['view'] = cols[4].xpath('./a/@href').get()
                appItem2['key']=appKey
        
            elif len(cols) == 6:  # If the table has 6 columns
                appItem2['datePub'] = cols[1].xpath('./text()').get()
                appItem2['doctype'] = cols[2].xpath('./text()').get()
                appItem2['desc'] = cols[4].xpath('./text()').get()
                appItem2['view'] = cols[5].xpath('./a/@href').get()
                appItem2['key']=appKey
            else:
                appItem2['datePub'] = cols[1].xpath('./text()').get()
                appItem2['doctype'] = cols[2].xpath('./text()').get()
                appItem2['desc'] = cols[-2].xpath('./text()').get()
                appItem2['view'] = cols[-1].xpath('./a/@href').get()
                appItem2['key']=appKey

            
            yield appItem2 # Yield each row as a separate item
      

