# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
class GenericcouncilItem(scrapy.Item):
    # define the fields for your item here like:
    applicationType = scrapy.Field() #
    address = scrapy.Field()#
    applicantName = scrapy.Field()#
    applicantAddress = scrapy.Field()#
    agentName = scrapy.Field()#
    agentEmail = scrapy.Field()   #   
    agentPhone = scrapy.Field() #
    agentMobile = scrapy.Field()#
    agentAddress = scrapy.Field()#
    key = scrapy.Field()#
    proposal = scrapy.Field()#



class DocumentsItem(scrapy.Item):
    datePub=scrapy.Field()
    doctype=scrapy.Field()
    desc=scrapy.Field()
    view=scrapy.Field()
    key=scrapy.Field()

class GeneralItem(scrapy.Item):
    applicationType = scrapy.Field() #
    address = scrapy.Field()#
    applicantName = scrapy.Field()#
    applicantAddress = scrapy.Field()#
    agentName = scrapy.Field()#
    agentEmail = scrapy.Field()   #   
    agentPhone = scrapy.Field() #
    agentMobile = scrapy.Field()#
    agentAddress = scrapy.Field()#
    key = scrapy.Field()#
    proposal = scrapy.Field()#
    datePub=scrapy.Field()
    doctype=scrapy.Field()
    desc=scrapy.Field()
    view=scrapy.Field()
    key=scrapy.Field()
