
from scrapy.exceptions import NotConfigured
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium import webdriver


class SeleniumMiddlewareArgs:
    """Selenium Middleware Args for input

    Settings's Parameters
    ----------
    SELENIUM_ENABLE: enable disable
        default False
        F
    SELENIUM_DRIVER_NAME: Selenium driver name 
        default "chrome"

    SELENIUM_DRIVER_ARGUMENTS: Selenium option args its array of string
        or you can use SELENIUM_WEBDRIVER_CHROME_OPTIONS

    SELENIUM_WEBDRIVER_CHROME_OPTIONS: its instant of selenium.webdriver.ChromeOptions 
        default None

    SELENIUM_DRIVER_EXECUTABLE_PATH: driver exe path
        default None

        
    Settings's Default Request Parameters
    ----------

    SELENIUM_DEFAULT_REQUEST_TIME_SLEEP_MILLI_SEC: time sleep in milli sec
    SELENIUM_DEFAULT_REQUEST_IMPLICITLY_WAIT: implicitly wait by selenium property
    SELENIUM_DEFAULT_REQUEST_PAGE_SOURCE_AS_BODY: its selenium driver page loaded in scrapy response default is True
    SELENIUM_DEFAULT_REQUEST_WAIT_TIME: wait time by wait untill in selenium
    SELENIUM_DEFAULT_REQUEST_WAIT_UNTIL: wait untill in selenium
    SELENIUM_DEFAULT_REQUEST_SCREENSHOT: take screenshot default is False
    SELENIUM_DEFAULT_REQUEST_SCRIPT: after page load execute javascript in selenium
    SELENIUM_DEFAULT_REQUEST_SCRIPT_AFTER_TIME_SLEEP_MILLI_SEC: after execute javascript wait for times

    """
    
    spider = None
    selenium_enable=False

    use_driver_manually_created = None
    callable_driver_created=None

    #options
    driver_name = "chrome"
    browser_executable_path = None
    driver_arguments = None

    #enabel screen recorder 
    driver_screen_recorder = False
    #driver_screen_recording_file_path_root = None
    driver_screen_recording_file_name = None

    #overrdier
    webdriverChromeOptions=None

    #SeleniumRequest default params
    default_request_time_sleep_millisec=None
    default_request_implicitly_wait=None
    default_request_page_source_as_body=None
    default_request_wait_time=None
    default_request_wait_until=None
    default_request_screenshot=None
    default_request_script=None

    default_request_script_after_time_sleep_millisec=None

    def load_setting(self,crawler):
        self.spider = crawler.spider

        self.selenium_enable = crawler.settings.get('SELENIUM_ENABLE')
        if self.selenium_enable == None:
            self.selenium_enable = False

        self.driver_screen_recorder = crawler.settings.get('DRIVER_SCREEN_RECORDER')
        if self.driver_screen_recorder == None:
            self.driver_screen_recorder = False
        #self.driver_screen_recording_file_path_root = crawler.settings.get('DRIVER_SCREEN_RECORDING_FILE_PATH_ROOT')
        self.driver_screen_recording_file_name = crawler.settings.get('DRIVER_SCREEN_RECORDING_FILE_NAME')


        self.use_driver_manually_created = crawler.settings.get('SELENIUM_USE_DRIVER_MANUALLY_CREATED')
        self.callable_driver_created = crawler.settings.get('SELENIUM_CALLABLE_DRIVER_CREATED')

        self.driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        self.driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')
        self.webdriverChromeOptions = crawler.settings.get('SELENIUM_WEBDRIVER_CHROME_OPTIONS')

        self.browser_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')

        if self.driver_screen_recorder == True:
            if self.driver_screen_recording_file_name == None:
                raise NotConfigured('driver_screen_recording_file_name must be set')
            #if self.driver_screen_recording_file_path_root == None:
            #    raise NotConfigured('DRIVER_SCREEN_RECORDING_FILE_PATH_ROOT must be set')

        if self.use_driver_manually_created == None:
            if self.driver_name is None:
                crawler.spider.log("default SELENIUM_DRIVER_NAME is chrome")
                self.driver_name = "chrome"

            if self.selenium_enable == True:
                if self.browser_executable_path == None and self.driver_name == "chrome":
                    crawler.spider.log("chrome driver download auto by ChromeDriverManager")
                    self.browser_executable_path = ChromeDriverManager().install()

                if self.browser_executable_path == None:
                    raise NotConfigured('SELENIUM_DRIVER_EXECUTABLE_PATH must be set')
                
                #validation
                if self.webdriverChromeOptions != None:
                    if not isinstance(self.webdriverChromeOptions, webdriver.ChromeOptions):
                        raise NotConfigured('SELENIUM_WEBDRIVER_CHROME_OPTIONS is not instance of webdriver.ChromeOptions')

            if self.driver_name is None and self.selenium_enable == True:
                raise NotConfigured('SELENIUM_DRIVER_NAME must be set')
        else:
            crawler.spider.log("chrome driver used manually created ...")

        #load req props
        self.default_request_time_sleep_millisec = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_TIME_SLEEP_MILLI_SEC")
        self.default_request_implicitly_wait = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_IMPLICITLY_WAIT")
        self.default_request_page_source_as_body = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_PAGE_SOURCE_AS_BODY")
        self.default_request_wait_time = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_WAIT_TIME")
        self.default_request_wait_until = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_WAIT_UNTIL")
        self.default_request_screenshot = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_SCREENSHOT")
        self.default_request_script = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_SCRIPT")

        self.default_request_script_after_time_sleep_millisec = crawler.settings.get("SELENIUM_DEFAULT_REQUEST_SCRIPT_AFTER_TIME_SLEEP_MILLI_SEC")

