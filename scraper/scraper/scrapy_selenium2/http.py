"""This module contains the ``SeleniumRequest`` class"""

from scrapy import Request
import time

from .utils import SeleniumMiddlewareArgs

class SeleniumRequest(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    def __init__(self, time_sleep_millisec =None, implicitly_wait=None, page_source_as_body=True ,wait_time=None, wait_until=None, 
                 screenshot=False, script=None, script_after_time_sleep_millisec = None ,*args, **kwargs):
        """Initialize a new selenium request

        Parameters
        ----------
        time_sleep_millisec: int
            Sleep and wait for times its milli sec

        implicitly_wait: int
            Call selenium driver method implicitly_wait after page load

        page_source_as_body:
            Its selenium driver page html load in scrapy response if pass True
            Default its True   

        wait_time: int
            The number of seconds to wait.
        wait_until: method
            One of the "selenium.webdriver.support.expected_conditions". The response
            will be returned until the given condition is fulfilled.
        screenshot: bool
            If True, a screenshot of the page will be taken and the data of the screenshot
            will be returned in the response "meta" attribute.
        script: str
            JavaScript code to execute.

        script_after_time_sleep_millisec: int
            if it will run script code then after inject script 
            wait for given times (Sleep and wait)

        """

        self.wait_time = wait_time
        self.wait_until = wait_until
        self.screenshot = screenshot
        self.script = script

        self.script_after_time_sleep_millisec = script_after_time_sleep_millisec

        self.implicitly_wait = implicitly_wait
        self.time_sleep_millisec = time_sleep_millisec
        self.page_source_as_body = page_source_as_body

        if time_sleep_millisec != None:
            self.time_sleep_millisec = (time_sleep_millisec / 1000)

        super().__init__(*args, **kwargs)

    def applyDefault(self, args: SeleniumMiddlewareArgs):
        #load default props 

        if self.wait_time == None:
            self.wait_time = args.default_request_wait_time

        if self.wait_until == None:
            self.wait_until = args.default_request_wait_until

        if self.script == None:
            self.script = args.default_request_script

        if self.implicitly_wait == None:
            self.implicitly_wait = args.default_request_implicitly_wait

        if self.time_sleep_millisec == None:
            self.time_sleep_millisec = args.default_request_time_sleep_millisec

        if self.script_after_time_sleep_millisec == None:
            self.script_after_time_sleep_millisec = args.default_request_script_after_time_sleep_millisec

        #handle boolean value
        if args.default_request_screenshot != None:
            self.screenshot = args.default_request_screenshot

        if args.default_request_page_source_as_body != None:
            self.page_source_as_body = args.default_request_page_source_as_body
 
        pass


class SeleniumRequestUpdatePageSourceAsBody(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    def __init__(self, page_source_as_html = None, *args, **kwargs):
        """Initialize a new selenium request

        Parameters
        ----------
        page_source_as_html: html string text
            update in scrapy body text and pass next

        """

        self.page_source_as_html = page_source_as_html

        super().__init__(*args, **kwargs)

