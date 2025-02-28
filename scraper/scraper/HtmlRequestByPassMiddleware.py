
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy import Request
from urllib.parse import urlparse,urlencode
import requests

import time
from ratelimiter import RateLimiter

class HtmlRequestByPass(Request):
    def __init__(self, content_status=200, content_body=None, content_encoding='utf8', *args, **kwargs):

        self.content_status = content_status
        self.content_body = content_body
        self.content_encoding = content_encoding

        # callback = kwargs.pop('callback', None)
        # callback=callback
        #dont_filter=True
        dont_filter = kwargs.pop('dont_filter', None)
        if dont_filter == None:
            dont_filter = True

        super().__init__(*args, dont_filter=dont_filter ,**kwargs)

class HtmlRequestRest(Request):
    def __init__(self, formdata=None, *args, **kwargs):
        self.formdata = formdata
        dont_filter = kwargs.pop('dont_filter', None)
        if dont_filter == None:
            #dont_filter = True
            pass

        super().__init__(*args,dont_filter=dont_filter ,**kwargs)



class HtmlRequestByPassMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        if isinstance(request, HtmlRequestByPass):
            return self.process_request_by_pass(request, spider)

        if isinstance(request, HtmlRequestRest):
            return self.process_request_rest(request, spider)

        return None

    def spider_closed(self,spider):
        pass

    def process_request_by_pass(self, request, spider):
        htmlRes = HtmlResponse(
            url=request._url,
            status=request.content_status,
            body= request.content_body,
            encoding=request.content_encoding,
            request=request
        )
        assert htmlRes.status == request.content_status
        return htmlRes

    def process_request_rest(self, request, spider):
        url = request.url
        method = request.method
        formdata = request.formdata

        content_status = 200
        content_body = None
        content_encoding = None

        if formdata == None:
            response = requests.request( method , url)
            content_status = response.status_code
            content_body = response.text
            content_encoding = response.encoding
        else:
            payload = urlencode(formdata)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.request(method , url , headers=headers, data=payload)

            content_status = response.status_code
            content_body = response.text
            content_encoding = response.encoding
        
        if content_status != 200:
            spider.log(f"status code: {content_status} for url: {url}")

        htmlRes = HtmlResponse(
            url= url,
            status= content_status,
            body=  content_body,
            encoding= content_encoding,
            request=request
        )
        assert htmlRes.status == content_status
        return htmlRes


class RateLimiterHandler:
    enable = False
    def __init__(self, enable=False ,max_calls=2, period=5, spider=None):
        self.max_calls = max_calls
        self.period = period
        self.rate_limiter = RateLimiter(max_calls=self.max_calls, period=self.period, callback=self.limited)
        self.enable = enable
        self.spider = spider

    def limited(self ,until):
        duration = int(round(until - time.time()))
        if self.spider != None:
            self.spider.log( 'Rate limited, sleeping for {:d} seconds'.format(duration) )
        else:
            print('Rate limited, sleeping for {:d} seconds'.format(duration))

    def wait_until_next_request(self):
        if self.enable == False:
            return False
        with self.rate_limiter:
            pass
            return True
        return True


