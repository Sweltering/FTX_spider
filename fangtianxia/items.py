# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewHouseItem(scrapy.Item):
    province = scrapy.Field()  # # 省份
    city = scrapy.Field()  # 城市
    name = scrapy.Field()  # 小区名称
    price = scrapy.Field()  # 价格
    rooms = scrapy.Field()  # 几居室（列表）
    area = scrapy.Field()  # 面积
    address = scrapy.Field()  # 地址
    district = scrapy.Field()  # 行政区
    sale = scrapy.Field()  # 是否在售
    origin_url = scrapy.Field()  # 房天下详情页面的url


class ESFHouseItem(scrapy.Item):
    province = scrapy.Field()  # # 省份
    city = scrapy.Field()  # 城市
    name = scrapy.Field()  # 小区名称
    rooms = scrapy.Field()  # 几居室
    floor = scrapy.Field()  # 几层
    toward = scrapy.Field()  # 朝向
    year = scrapy.Field()  # 年代
    address = scrapy.Field()  # 地址
    area = scrapy.Field()  # 面积
    price = scrapy.Field()  # 总价
    unit = scrapy.Field()  # 单价
    origin_url = scrapy.Field()
