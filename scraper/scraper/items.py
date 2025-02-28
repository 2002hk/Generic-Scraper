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
    applicationType = scrapy.Field()
    address = scrapy.Field()
    applicantName = scrapy.Field()
    applicantAddress = scrapy.Field()
    parish = scrapy.Field()
    ward = scrapy.Field()
    agentName = scrapy.Field()
    agentEmail = scrapy.Field()      
    agentPhone = scrapy.Field() 
    agentMobile = scrapy.Field()
    agentFax = scrapy.Field()
    agentAddress = scrapy.Field()
    key = scrapy.Field()
    documentsLink = scrapy.Field()
    applicationForm = scrapy.Field()
    decisionNotice = scrapy.Field()
    proposal = scrapy.Field()
    decisionDate = scrapy.Field()
    '''
    psSearchDecision = scrapy.Field()
    psSurname = scrapy.Field()
    psPostCode = scrapy.Field()
    psSearchUrl1 = scrapy.Field()
    psResult1 = scrapy.Field()
    psResultCount1 = scrapy.Field()
    psSearchUrl2 = scrapy.Field()
    psResult2 = scrapy.Field()
    psResultCount2 = scrapy.Field()
    '''
    
    agentCompanyName = scrapy.Field()
    reference=scrapy.Field()
    altref=scrapy.Field()
    apprecv=scrapy.Field()
    appvalid=scrapy.Field()
    status=scrapy.Field()
    decision=scrapy.Field()
    decision_issue_date=scrapy.Field()
    appeal_status=scrapy.Field()
    appeal_decision=scrapy.Field()
    actual_decision_level=scrapy.Field()
    expected_decision_level=scrapy.Field()
    case_officer=scrapy.Field()
    agent_address=scrapy.Field()


class DocumentsItem(scrapy.Item):
    datePub=scrapy.Field()
    doctype=scrapy.Field()
    desc=scrapy.Field()
    view=scrapy.Field()
