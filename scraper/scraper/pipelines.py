# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv
from scraper.items import GenericcouncilItem
from scraper.items import DocumentsItem
from scraper.items import HaringeyItems
from scraper.items import HaveringItem
from scraper.items import CamdenItems

class ScraperPipeline:
    def process_item(self, item, spider):
        return item

class GenericcouncilPipeline:
    def open_spider(self, spider):
        # Open CSV file for writing
        self.file = open('mainpageitems_scrapy_barnet.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        
        # Writing the header row with all field names
        self.writer.writerow([
            'applicationType', 'address', 'applicantName', 'applicantAddress',
            'agentName', 'agentEmail', 'agentPhone', 'agentMobile', 'agentAddress',
            'key',  'proposal'
        ])
    
    def process_item(self, item, spider):
        # Convert Scrapy item to a dictionary
        if isinstance(item, GenericcouncilItem):
            item = dict(item)
        
        # Write item values in the CSV file in the same order as headers
            self.writer.writerow([
                item.get('applicationType', ''), item.get('address', ''), item.get('applicantName', ''),
                item.get('applicantAddress', ''),
                item.get('agentName', ''), item.get('agentEmail', ''), item.get('agentPhone', ''),
                item.get('agentMobile', ''),  item.get('agentAddress', ''),
                item.get('key', ''),  
                item.get('proposal', ''), 
                
        ])
        return item
    
    def close_spider(self, spider):
        # Close CSV file when the spider is finished
        self.file.close()

class DocumentsPipeline:
    def open_spider(self, spider):
        # Open CSV file for writing
        self.file2 = open('documents_scrapy_barnet.csv', 'w', newline='', encoding='utf-8')
        self.writer2 = csv.writer(self.file2)
        
        # Writing the header row with all field names
        self.writer2.writerow(['datePub', 'doctype', 'desc', 'view','key'])
    
    def process_item(self, item, spider):
        # Convert Scrapy item to a dictionary
        if isinstance(item, DocumentsItem):
            item = dict(item)
        
        # Write item values in the CSV file in the same order as headers
            self.writer2.writerow([
                item.get('datePub', ''), item.get('doctype', ''), item.get('desc', ''), item.get('view', ''),item.get('key', '')
            ])
        return item
    
    def close_spider(self, spider):
        # Close CSV file when the spider is finished
        self.file2.close()
class HaringeyPipeline:
    def open_spider(self, spider):
        # Open CSV file for writing
        self.file3 = open('haringey_data.csv', 'w', newline='', encoding='utf-8')
        self.writer3 = csv.writer(self.file3)
        
        # Writing the header row with all field names
        self.writer3.writerow([
            'appref', 'proposal', 'appstatus', 'siteadd',
            'datevalid', 'decision', 'decisionNotice'
        ])
    
    def process_item(self, item, spider):
        # Convert Scrapy item to a dictionary
        if isinstance(item, HaringeyItems):
            item = dict(item)
        
        # Write item values in the CSV file in the same order as headers
            self.writer3.writerow([
                item.get('appref', ''), item.get('proposal', ''), item.get('appstatus', ''),item.get('siteadd', ''),
                item.get('datevalid', ''),
                item.get('decision', ''), item.get('decisionNotice', '')
                
        ])
        return item
    
    def close_spider(self, spider):
        # Close CSV file when the spider is finished
        self.file3.close()

class HaveringPipeline:
    def open_spider(self, spider):
        # Open CSV file for writing
        self.file4 = open('havering_data.csv', 'w', newline='', encoding='utf-8')
        self.writer4 = csv.writer(self.file4)
        
        # Writing the header row with all field names
        self.writer4.writerow([
            'reference', 'location', 'proposal', 'status'
        ])
    
    def process_item(self, item, spider):
        # Convert Scrapy item to a dictionary
        if isinstance(item, HaveringItem):
            item = dict(item)
        
        # Write item values in the CSV file in the same order as headers
            self.writer4.writerow([
                item.get('reference', ''), item.get('location', ''), item.get('proposal', ''),item.get('status', '')
              
                
        ])
        return item
    
    def close_spider(self, spider):
        # Close CSV file when the spider is finished
        self.file4.close()

class CamdenPipeline:
    def open_spider(self, spider):
        # Open CSV file for writing
        self.file5 = open('camden_data.csv', 'w', newline='', encoding='utf-8')
        self.writer5 = csv.writer(self.file5)
        
        # Writing the header row with all field names
        self.writer5.writerow([
            'decision', 'appno', 'siteAdd', 'appType','proposal','applicant'
        ])
    
    def process_item(self, item, spider):
        # Convert Scrapy item to a dictionary
        if isinstance(item, CamdenItems):
            item = dict(item)
        
        # Write item values in the CSV file in the same order as headers
            self.writer5.writerow([
                item.get('decision', ''), item.get('appno', ''), item.get('siteAdd', ''),item.get('appType', ''),
                item.get('proposal', ''), item.get('applicant', '')
              
                
        ])
        return item
    
    def close_spider(self, spider):
        # Close CSV file when the spider is finished
        self.file5.close()
