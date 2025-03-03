# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv
from scraper.items import GenericcouncilItem
from scraper.items import DocumentsItem

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

