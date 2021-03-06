import urllib2
import urlparse
import re
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup


class PopcornTV:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:32.0) Gecko/20100101 Firefox/32.0"

    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getCategories(self):
        pageUrl = "http://home.popcorntv.it/"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        categories = []
        list = tree.findAll("div", "container-mega")
        for item in list:
            link = item.parent.find("a")
            category = {}
            category["title"] = link.text.strip()
            category["url"] = link["href"]
            categories.append(category)
       
        return categories

    def getSubCategories(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        urlParsed = urlparse.urlsplit(pageUrl)
        urlSite = urlParsed.scheme + "://" + urlParsed.netloc

        subcategories = []
        list = htmlTree.findAll("div", "lista-serie")
        for item in list:
            link = item.find("a")
            subcategory = {}
            subcategory["title"] = link.text.strip()
            subcategory["url"] = link["href"]
            if not subcategory["url"].startswith("http"):
                subcategory["url"] = urlSite + subcategory["url"]
            # Don't insert duplicate items
            if subcategory not in subcategories:
                subcategories.append(subcategory)
            
        return subcategories
        
    def getVideoBySubCategories(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        videoList = []
        
        if pageUrl.startswith("http://ladychannel.popcorntv.it/"):
            # LadyChannel: show video only in "Tutti gli episodi"
            items = htmlTree.findAll("div", "serie-gridview")[1].findAll("a")
        else:
            items = htmlTree.find("h1", "headings-episodi").parent.findAll("a")
        
        for item in items:
            video = {}
            video["title"] = item["title"].strip()
            video["url"] = item["href"]
            video["thumb"] = item.find("img")["src"]
            videoList.append(video)
            
        # Get pagination URLs
        nextPageUrl = None
        firstPageUrl = None
        lastPageUrl = None
        prevPageUrl = None

        pagination = htmlTree.find("ul", "pagination")
        if pagination is not None:
            prevPage = pagination.find("a", {"rel": "prev"})
            if prevPage is not None:
                prevPageUrl = prevPage["href"]
                firstPage = prevPage.parent.findNextSibling("li").find("a")
                firstPageUrl = firstPage["href"]
                
            nextPage = pagination.find("a", {"rel": "next"})
            if nextPage is not None:
                nextPageUrl = nextPage["href"]
                lastPage = nextPage.parent.findPreviousSibling("li").find("a")
                lastPageUrl = lastPage["href"]
            
        page = {}
        page["videoList"] = videoList
        page["prevPageUrl"] = prevPageUrl
        page["firstPageUrl"] = firstPageUrl
        page["lastPageUrl"] = lastPageUrl
        page["nextPageUrl"] = nextPageUrl
        return page

    def getVideoMetadata(self, pageUrl):
        metadata = {}
        
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        metadata["title"] = htmlTree.find("header","video-heading").text.strip()
        metadata["thumb"] = htmlTree.find("meta", {"property": "og:image"})['content']
        
        match=re.compile('\("vplayerPopcorn","1020","550","(.+?)"').findall(data)
        metadata["smilUrl"] = match[0]
        # Remove spaces from smil URL
        metadata["smilUrl"] = metadata["smilUrl"].replace(" ","")
        
        return metadata
        
    def getVideoURL(self, smilUrl, quality=1200):
        data = urllib2.urlopen(smilUrl).read()
        htmlTree=BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
        
        base = htmlTree.find('meta')['base']

        # Get the best available bitrate
        hbitrate = -1
        sbitrate = int(quality) * 1024
        for item in htmlTree.findAll('video'):
            try:
                bitrate = int(item['system-bitrate'])
            except KeyError:
                bitrate = 0
            if bitrate > hbitrate and bitrate <= sbitrate:
                hbitrate = bitrate
                filepath = item['src']

        url = base + " playpath=" + filepath
        return url
