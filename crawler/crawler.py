import logging
import re
from urllib.parse import urlparse
from corpus import Corpus
import os
import lxml.html
from collections import deque

logger = logging.getLogger(__name__)

class Crawler:
    """
    This class is responsible for scraping urls from the next available link in frontier and adding the scraped links to
    the frontier
    """

    def __init__(self, frontier):
        self.frontier = frontier
        self.corpus = Corpus()
        self.mostValidOut = 0
        self.mostValidOutURL = ""
        self.listTraps = []
        self.subdomainCount = {}
        self.prev_query = []
        self.param = ""
        self.count = 0
        self.urldeque = deque(maxlen=10)

    def start_crawling(self):
        """
        This method starts the crawling process which is scraping urls from the next available link in frontier and adding
        the scraped links to the frontier
        """
        while self.frontier.has_next_url():
            url = self.frontier.get_next_url()
            logger.info("Fetching URL %s ... Fetched: %s, Queue size: %s", url, self.frontier.fetched, len(self.frontier))
            url_data = self.fetch_url(url)
            self.prev_query = []
            self.param = ""
            self.count = 0
            count_valid_URLs = 0
            for next_link in self.extract_next_links(url_data):
                if self.corpus.get_file_name(next_link) is not None:
                    if self.is_valid(next_link):
                        self.urldeque.append(next_link)
                        count_valid_URLs+=1
                        if not self.frontier.is_duplicate(next_link):
                            parsed = urlparse(next_link)
                            if parsed.netloc not in self.subdomainCount:
                                self.subdomainCount[parsed.netloc] = 1
                            else:
                                self.subdomainCount[parsed.netloc] += 1
                        self.frontier.add_url(next_link)
            if count_valid_URLs > self.mostValidOut:
                self.mostValidOut = count_valid_URLs
                self.mostValidOutURL = url_data['url']
                
        analyticsA1A2 = open('A1A2.txt',mode='w')
        analyticsA1A2.write('URLs processed from each subdomain:\n')
        for k,v in sorted(self.subdomainCount.items(),key=lambda x: x[1],reverse=True):
            analyticsA1A2.write('{} : {}\n'.format(k,v))
        analyticsA1A2.write('\nMost Valid Out Links: {} with {}'.format(self.mostValidOutURL,self.mostValidOut))

        analyticsA3URLs = open('A3URLs.txt',mode='w')
        analyticsA3URLs.write('List of Downloaded URLS:\n')
        for url in list(self.frontier.urls_set):
            analyticsA3URLs.write('{}\n'.format(url))

        analyticsA3Traps = open('A3Traps.txt',mode='w')
        analyticsA3Traps.write('List of Traps:\n')
        for trap in self.listTraps:
            analyticsA3Traps.write('{}\n'.format(trap))

        analyticsA1A2.close()
        analyticsA3URLs.close()
        analyticsA3Traps.close()
                

    def fetch_url(self, url):
        """
        This method, using the given url, should find the corresponding file in the corpus and return a dictionary
        containing the url, content of the file in binary format and the content size in bytes
        :param url: the url to be fetched
        :return: a dictionary containing the url, content and the size of the content. If the url does not
        exist in the corpus, a dictionary with content set to None and size set to 0 can be returned.
        """
        file_address = self.corpus.get_file_name(url)
        if file_address == None:
            url_data = {
                "url": url,
                "content": None,
                "size": 0
            }
        file = open(file_address,'rb')
        content = file.read()
        size = os.path.getsize(file_address)
        url_data = {"url":url,"content":content,"size":size}
        return url_data

    def extract_next_links(self, url_data):
        """
        The url_data coming from the fetch_url method will be given as a parameter to this method. url_data contains the
        fetched url, the url content in binary format, and the size of the content in bytes. This method should return a
        list of urls in their absolute form (some links in the content are relative and needs to be converted to the
        absolute form). Validation of links is done later via is_valid method. It is not required to remove duplicates
        that have already been fetched. The frontier takes care of that.

        Suggested library: lxml
        """
        html = lxml.html.fromstring(url_data['content'])
        html.make_links_absolute(url_data['url'],resolve_base_href=True)
        links = html.xpath('//a/@href')
        return links

    def is_valid(self, url):
        """
        Function returns True or False based on whether the url has to be fetched or not. This is a great place to
        filter out crawler traps. Duplicated urls will be taken care of by frontier. You don't need to check for duplication
        in this method
        """
        parsed = urlparse(url)
        q_components = re.split('=|&', parsed.query)
        length = 0
        counter = 0
        too_close = 0
        for each in self.urldeque:
            parsed1 = urlparse(url)
            parsed2 = urlparse(each)
            q_components1 = re.split('=|&', parsed1.query)
            q_components2 = re.split('=|&', parsed2.query)
            if parsed1.netloc == parsed2.netloc \
               and parsed1.path == parsed2.path \
               and parsed1.params == parsed2.params \
               and len(q_components1) == len(q_components2):
                maybe_close = 0
                for each in range(0, len(q_components1)):
                    if q_components1[each] == q_components2[each]:
                        maybe_close += 1
                    if maybe_close/len(q_components1) >= .5:
                        too_close += 1
                    if too_close == 10:
                        return False
        if len(q_components) > len(self.prev_query):
            length = len(self.prev_query)
        else:
            length = len(q_components)
        if length != 0:
            for each in range(0, length - 1):
                if q_components[each] == self.prev_query[each]:
                    counter += 1
                    if self.count >= 15:
                        self.listTraps.append(url)
                        return False
            if counter/length >= .5 and parsed.params == self.param:
                self.count += 1
        self.prev_query = q_components
        self.param = parsed.params
        if parsed.scheme not in set(["http", "https"]):
            return False
        if parsed.path != '':
            directories = parsed.path.split("/")
            if len(directories) > 15:
                self.listTraps.append(url)
                return False
            for sub in directories:
                if directories.count(sub) > 5:
                    self.listTraps.append(url)
                    return False
        try:
            return ".ics.uci.edu" in parsed.hostname \
                   and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4" \
                                    + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
                                    + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
                                    + "|thmx|mso|arff|rtf|jar|csv" \
                                    + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower())

        except TypeError:
            print("TypeError for ", parsed)
            return False

