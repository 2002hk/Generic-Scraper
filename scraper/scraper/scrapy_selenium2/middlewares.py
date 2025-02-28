"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""

from importlib import import_module

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import time
from .http import SeleniumRequest, SeleniumRequestUpdatePageSourceAsBody
from .utils import SeleniumMiddlewareArgs
from urllib.parse import urlparse, ParseResult

class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""
        
        args = SeleniumMiddlewareArgs()
        args.load_setting(crawler)

        middleware = cls(
            args=args
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)

        return middleware

    def __init__(self, args: SeleniumMiddlewareArgs ):
        """Initialize the selenium webdriver

        Parameters
        ----------
        args: SeleniumMiddlewareArgs
            The selenium ``WebDriver`` to props
        """

        if args.selenium_enable == False:
            self.driver = None
            args.spider.log("selenium driver is disabled")
            return None

        if args.use_driver_manually_created == None:

            webdriver_base_path = f'selenium.webdriver.{args.driver_name}'

            driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
            driver_klass = getattr(driver_klass_module, 'WebDriver')

            driver_options_module = import_module(f'{webdriver_base_path}.options')
            driver_options_klass = getattr(driver_options_module, 'Options')

            driver_service_module = import_module(f'{webdriver_base_path}.service')
            driver_service_klass = getattr(driver_service_module, 'Service')


            driver_options = None

            if args.webdriverChromeOptions != None:
                args.spider.log("selenium driver loaded webdriverChromeOptions from setting")
                driver_options = args.webdriverChromeOptions
            else:
                driver_options = driver_options_klass()

            if args.webdriverChromeOptions == None:
                for argument in args.driver_arguments:
                    driver_options.add_argument(argument)
                    if argument == "--headless":
                        driver_options.headless = True
                        pass


            service_args = []
            driver_service = driver_service_klass(args.browser_executable_path,service_args)


            driver_kwargs = {
                'service': driver_service,
                'options': driver_options
            }

            self.driver = driver_klass(**driver_kwargs)
        
        else:
            self.driver = args.use_driver_manually_created

        args.spider.driver = self.driver
        args.spider.driver_default = args

        #callable
        if args.callable_driver_created != None:
            caller = args.callable_driver_created
            caller()

        #wait for maximum time 
        self.driver.implicitly_wait(60)

        #screen 
        self.screen_recorder = None

        if args.driver_screen_recorder == True:
            #requirements_screen_recorder = "humanize==4.3.0, loguru==0.6.0, numpy==1.23.2, opencv_python==4.6.0.66, Pillow==9.2.0, PyAutoGUI==0.9.53"
            args.spider.log("selenium driver screen_recorder enabled")
            #args.spider.log(f"requirements of screen_recorder: {requirements_screen_recorder}")
            from .selenium_video import VideoRecorder

            self.screen_recorder = VideoRecorder(driver=self.driver, filename= args.driver_screen_recording_file_name)
            self.screen_recorder.start()

            #screen_recorder_clazz_name = f'scrapy_selenium2.screen_recorder'
            #screen_recorder_klass_module = import_module(screen_recorder_clazz_name)
            #self.screen_recorder = screen_recorder_klass_module(driver=self.driver,file_path_root=args.driver_screen_recording_file_path_root,file_name=args.driver_screen_recording_file_name)
            #self.screen_recorder.record_screen()

        args.spider.screen_recorder = self.screen_recorder
            

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if isinstance(request,SeleniumRequestUpdatePageSourceAsBody):
            return self.process_selenium_request_update_page_source_as_body(request=request, spider=spider)

        if not isinstance(request, SeleniumRequest):
            return None


        spider.driver = self.driver
        args = None
        if hasattr(spider, 'driver_default'):
            args = spider.driver_default
            request.applyDefault(args)


        for cookie_name, cookie_value in request.cookies.items():
            spider.log(f'driver request.cookies load before request ...')
            self.driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': cookie_value
                }
            )

        spider.log(f'driver load url: {request.url}')
        self.driver.get(request.url)

        if request.implicitly_wait != None:
            spider.log(f'driver wailt ... time_sleep_millisec: {request.implicitly_wait}')
            self.driver.implicitly_wait(request.implicitly_wait)
        
        if request.time_sleep_millisec != None:
            spider.log(f'driver wailt ... time_sleep_millisec: {request.time_sleep_millisec}')
            time.sleep(request.time_sleep_millisec)

        if request.wait_until:
            spider.log(f'driver wait_until: {request.wait_until} and wait_time: {request.wait_time}')
            WebDriverWait(self.driver, request.wait_time).until(
                request.wait_until
            )

        current_url = self.driver.current_url


        if request.screenshot:
            spider.log(f'driver screenshot...')
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            spider.log(f'driver execute script...')
            self.driver.execute_script(request.script)

            request

        spider.log(f'driver page_source_as_body: {request.page_source_as_body} ...')
        body = None
        if request.page_source_as_body == True:
            body = str.encode(self.driver.page_source)

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})
        request.meta.update({'base_url': self.get_base_url(full_url=current_url,spider=spider) })

        return HtmlResponse(
            current_url,
            body=body,
            encoding='utf-8',
            request=request
        )
    
    def process_selenium_request_update_page_source_as_body(self, request:SeleniumRequestUpdatePageSourceAsBody, spider):
        spider.driver = self.driver

        spider.log(f'driver page source as body update request ...')
        current_url = self.driver.current_url

        body = request.page_source_as_html
        if body == None:
            body = str.encode(self.driver.page_source)

        
        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})
        request.meta.update({'base_url': self.get_base_url(full_url=current_url,spider=spider) })

        return HtmlResponse(
            current_url,
            body=body,
            encoding='utf-8',
            request=request
        )


    def get_base_url(self,full_url,spider):
        try:
            # Parse the URL
            parsed_url = urlparse(full_url)
            
            # Ensure the parsed URL is valid with both scheme and netloc
            if all([parsed_url.scheme, parsed_url.netloc]):
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                return base_url
            else:
                raise ValueError("Invalid URL: Missing scheme or netloc")
        
        except Exception as e:
            spider.log(f"Error get_base_url parse error : {e}")
            return None  # Or you can return an empty string '' if preferred


    def spider_closed(self,spider):
        """Shutdown the driver when spider is closed"""
        # if spider.driver_default.driver_screen_recorder == True:
        #     spider.log(f'screen recorder driver stopping...')
        #     try:
        #         self.screen_recorder.stop()
        #     except :
        #         print("screen recorder stopping error")

        spider.log(f'Shutdown driver ...')
        try:
            self.driver.quit()
        except :
            print("Shutdown driver.quit error")
