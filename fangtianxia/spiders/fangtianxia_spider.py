# -*- coding: utf-8 -*-
import scrapy
import re
from fangtianxia.items import NewHouseItem, ESFHouseItem
from scrapy_redis.spiders import RedisSpider


class FangtianxiaSpiderSpider(RedisSpider):
    name = 'fangtianxia_spider'
    allowed_domains = ['fang.com']
    # start_urls = ['http://www.fang.com/SoufunFamily.htm']
    redis_key = "fang:start_urls"

    # 解析省份、城市及其对应的新房、二手房url
    def parse(self, response):
        trs = response.xpath("//div[@class='outCont']//tr")  # 所有省份的tr标签
        province = None  # 保存省份信息
        for tr in trs:
            tds = tr.xpath(".//td[not(@class)]")  # 获取tr标签下的td标签（省份、城市，第一个td标签不需要）
            province_td = tds[0]  # 省份的td标签
            province_text = province_td.xpath(".//text()").get()  # 省份的名称
            province_text = re.sub(r"\s", "", province_text)  # 通过正则的sub函数匹配替换含有空格的省份td标签
            if province_text:  # 如果有文本，就将省份信息保留
                province = province_text

            # 除去其他海外的一些地区
            if province == "其它":
                continue

            city_td = tds[1]  # 城市的td标签
            city_links = city_td.xpath(".//a")  # 所有城市a标签
            for city_link in city_links:
                city = city_link.xpath(".//text()").get()  # 每个城市的名字
                city_url = city_link.xpath(".//@href").get()  # 每个城市的url

                # 获取到每个城市的url后，就可以构建新房的url和二手房的url
                url_module = city_url.split(".", 1)  # ['http://wuhu','fang.com/']
                scheme = url_module[0]
                domain = url_module[1]
                # 北京是特例，需要对其进行过滤
                if "bj" in scheme:
                    newhouse_url = "http://newhouse.fang.com/house/s/"
                    esf_url = "http://esf.fang.com/"
                else:
                    # 新房的url
                    newhouse_url = scheme + ".newhouse." + domain + "house/s/"
                    # 构建二手房的url
                    esf_url = scheme + ".esf." + domain

                # 对新房的url发起请求，并将之前解析的省份及城市信息传递给解析新房的函数
                yield scrapy.Request(url=newhouse_url, callback=self.parse_newhouse, meta={"info": (province, city)})

                # 对二手房的url发起请求，并将之前解析的省份及城市信息传递给解析二手房的函数
                yield scrapy.Request(url=esf_url, callback=self.parse_esf, meta={"info": (province, city)})

    # 解析新房的房源信息
    def parse_newhouse(self, response):
        province, city = response.meta.get("info")
        lis = response.xpath("//div[contains(@class, 'nl_con')]/ul/li")  # 每个房源的li标签
        for li in lis:
            name = li.xpath(".//div[@class='nlcd_name']/a/text()").get()  # 房源名称
            if not name == None:  # 有None类型的数据不去处理
                name = name.strip()
            house_type_list = li.xpath(".//div[contains(@class, 'house_type')]/a/text()").getall()  # 几居室
            if not len(house_type_list) == 0:  # 有空数据的不去处理
                rooms = house_type_list
            area = "".join(li.xpath(".//div[contains(@class, 'house_type')]/text()").getall())  # 面积
            area = re.sub(r"\s|－|/", "", area)
            address = li.xpath(".//div[@class='address']/a/@title").get()  # 地址
            district_text = "".join(li.xpath(".//div[@class='address']/a//text()").getall())  # 行政区
            district = re.search(r".*\[(.+)\].*", district_text)
            if not district == None:
                district = district.group(1)
            sale = li.xpath(".//div[contains(@class, 'fangyuan')]/span/text()").get()  # 是否在售
            price = "".join(li.xpath(".//div[@class='nhouse_price']//text()").getall())  # 价格
            price = re.sub(r"\s|广告", "", price)
            origin_url = li.xpath(".//div[@class='nlcd_name']/a/@href").get()

            item = NewHouseItem(
                province=province,
                city=city,
                name=name,
                rooms=rooms,
                area=area,
                address=address,
                district=district,
                sale=sale,
                price=price,
                origin_url=origin_url
            )
            yield item

        # 发送下一页的请求
        next_url = response.xpath(".//div[@class='page']//a[@class='next']/@href").get()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url),
                                 callback=self.parse_newhouse, meta={"info": (province, city)})

    # 解析二手房的房源信息
    def parse_esf(self, response):
        province, city = response.meta.get("info")
        dls = response.xpath("//div[@class='houseList']/dl")  # 所有二手房的dl标签
        for dl in dls:
            item = ESFHouseItem(province=province, city=city)
            item["name"] = dl.xpath(".//p[@class='mt10']/a/span/text()").get()  # 房源名称
            infos = dl.xpath(".//p[@class='mt12']/text()").getall()  # 房源信息
            infos = list(map(lambda x:re.sub(r"\s", "", x), infos))
            for info in infos:
                if "厅" in info:
                    item['rooms'] = info
                elif "层" in info:
                    item["floor"] = info
                elif "向" in info:
                    item["toward"] = info
                else:
                    item['year'] = info.replace("建筑年代：", "")
            item['address'] = dl.xpath(".//p[@class='mt10']/span/@title").get()  # 地址
            item['area'] = dl.xpath(".//div[contains(@class, 'area')]/p/text()").get()  # 面积
            item["price"] = "".join(dl.xpath(".//div[@class='moreInfo']/p[1]//text()").getall())  # 总价
            item["unit"] = "".join(dl.xpath(".//div[@class='moreInfo']/p[2]//text()").getall())  # 单价
            detail_url = dl.xpath(".//p[@class='title']/a/@href").get()
            item["origin_url"] = response.urljoin(detail_url)

            yield item

        # 再次请求发送下一页的url
        next_url = response.xpath("//a[@id='PageControll_hlk_next']/@href").get()
        yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_esf, meta={"into": (province, city)})


