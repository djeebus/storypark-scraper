import scrapy


class StoryparkItem(scrapy.Item):
    image_url = scrapy.Field()
    filename = scrapy.Field()
