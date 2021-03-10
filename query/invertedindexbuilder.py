from corpus import Corpus
import pickle
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from urllib.parse import urlparse
from math import log10

class InvertedIndexBuilder:
    """
    This class is responsible for building the inverted index for our search engine
    """

    def __init__(self):
        self.corpus = Corpus()
        self.validurls = pickle.load(open('url_set.pkl',"rb"))
        self.invertedIndex = {}

    def start_building(self):
        """
        This method starts the building process which is getting the urls from the corpus
        using the bookkeeping json file
        """
        for url in self.validurls:
            url_data = self.fetch_url(url)
            soup = BeautifulSoup(url_data['content'],features="lxml")
            for script in soup(["script","style"]):
                script.extract()
            text = soup.get_text()
            stopWords = set(stopwords.words('english'))
            tokenizer = RegexpTokenizer(r'\w+')
            words = tokenizer.tokenize(text)
            wordsFiltered = []
            lemmatizer = WordNetLemmatizer()
            for w in words:
                if w not in stopWords:
                    wordsFiltered.append(lemmatizer.lemmatize(w.lower()))
            doc_id = self.get_doc_id(url)
            self.add_to_index(wordsFiltered,doc_id)
        for token in self.invertedIndex:
            self.invertedIndex[token][1] = log10(len(self.validurls) / len(self.invertedIndex[token][0]))
            for docu in self.invertedIndex[token][0]:
                self.invertedIndex[token][0][docu][1] = 1 + log10(self.invertedIndex[token][0][docu][0])
                self.invertedIndex[token][0][docu][2] = (self.invertedIndex[token][0][docu][1]) * (self.invertedIndex[token][1])
        invertedIndex_file = open("inverted_index.pkl","wb")
        pickle.dump(self.invertedIndex, invertedIndex_file)
        

    def get_doc_id(self,url):
        """
        This method, using the given url, finds the corresponding file in the corpus
        and returns the doc ID
        """
        url = url.strip()
        parsed_url = urlparse(url)
        url = url[len(parsed_url.scheme)+3:]
        return self.corpus.url_file_map[url]

    def add_to_index(self,wordsFiltered,doc_id):
        for word in wordsFiltered:
            if word not in self.invertedIndex:
                self.invertedIndex[word] = [{doc_id:[1, 0, 0]}, 0]
            elif any(doc_id == key for key in self.invertedIndex[word][0]) == False:
                self.invertedIndex[word][0].update({doc_id:[1, 0, 0]})
            else:
                self.invertedIndex[word][0][doc_id][0] += 1
                
    def fetch_url(self,url):
        """
        This method, using the given url, should find the corresponding file in the corpus and return a dictionary
        containing the url, content of the file in binary format and the content size in bytes
        :param url: the url to be fetched
        :return: a dictionary containing the url, content and the size of the content. If the url does not
        exist in the corpus, a dictionary with content set to None and size set to 0 can be returned.
        """
        file_address = self.corpus.get_file_name(url)
        if file_address == None: url_data = {"url":url, "content":None}
        file = open(file_address,'rb')
        content = file.read()
        url_data = {"url":url,"content":content}
        return url_data



i = InvertedIndexBuilder()
i.start_building()
