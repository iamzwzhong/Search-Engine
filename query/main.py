import tkinter
import webbrowser
import efficient_scoring
import pickle
import corpus
from bs4 import BeautifulSoup
from functools import partial
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import os

class Search_Engine:
    def __init__(self):
        self.window = tkinter.Tk()
        self.index = pickle.load(open('inverted_index.pkl',"rb"))
        self.corpus = corpus.Corpus()

    def run(self):
        """
        Sets up the GUI for user to input a query
        """
        
        self.window.title('CS 121 Search Engine')
        self.window.config(background="gray29")
        self.window.geometry('800x250')

        #Create main frames
        top_frame = tkinter.Frame(self.window,bg="gray29",width=750,height=150,pady=20)
        ctr_frame = tkinter.Frame(self.window,bg="gray29",width=750,height=100)
        btm_frame = tkinter.Frame(self.window,bg="gray29",width=800,height=50)

        #Layout main frames
        self.window.grid_rowconfigure(1,weight=1)
        self.window.grid_columnconfigure(0,weight=1)

        top_frame.grid(row=0,sticky="s")
        ctr_frame.grid(row=1,sticky="n")
        btm_frame.grid(row=3,sticky="WENS")


        #top frame
        title = tkinter.Label(top_frame, text="Search Engine",\
                            bg="gray29",fg="white",font=("Arial",40))
        title.grid(row=0,column=0)

        #create center frames
        ctr_left = tkinter.Frame(ctr_frame,bg="gray29",width=600,height=100,padx=10,pady=10)
        ctr_right = tkinter.Frame(ctr_frame,bg="gray29",width=200,height=100,padx=10,pady=10)

        ctr_left.grid(row=0,column=0)
        ctr_right.grid(row=0,column=1)
        
        self.searchbox = tkinter.Entry(ctr_left,width = 23,font=("Arial",25))
        self.searchbox.grid(row=0)

        def getContent():
            self.openResults(self.searchbox.get())
    
        searchbutton = tkinter.Button(ctr_right,command=getContent,text="Search",width = 10,font=("Arial",15))
        searchbutton.grid(row=0)

        #bottom frames
        btm_left = tkinter.Frame(btm_frame,bg="gray29",width=400,height=50,pady=10,padx=10)
        btm_right = tkinter.Frame(btm_frame,bg="gray29",width=400,height=50,pady=10,padx=350)

        btm_left.grid(row=0,column=0,sticky="w")
        btm_right.grid(row=0,column=1,sticky="e")

        class_name = tkinter.Label(btm_left, text="CS 121 Information Retrieval",\
                                bg = "gray29",fg="white smoke",font=("Arial",12))
        class_name.grid(row=0)

        our_names = tkinter.Label(btm_right, text = "Zhi Wen Zhong & Tyler Foey",\
                                bg = "gray29",fg="white smoke",font=("Arial",12))
        our_names.grid(row=0)
        
        self.window.mainloop()

    def hide(self):
        """
        Hides the initial page of the search engine
        """
        self.window.withdraw()

    def openResults(self,query):
        """
        Opens a new frame of the search engine that displays the results
        of the query inputted by the user
        """
        self.hide()
        otherFrame = tkinter.Toplevel()
        otherFrame.geometry('800x800')
        otherFrame.config(background="gray29")
        otherFrame.title("Search Results")
        otherFrame.grid_rowconfigure(1, weight=1)
        otherFrame.grid_columnconfigure(0,weight=1)

        display_top = tkinter.Frame(otherFrame, bg="gray29", width=750,height=150)
        display_top.grid(row=0,sticky="nw")
        display_bottom = tkinter.Frame(otherFrame,bg="gray29",width=750,height=650)
        display_bottom.grid(row=1,sticky="nw")

        handler = lambda:self.onBack(otherFrame)
        backButton = tkinter.Button(display_top,text="Back",command=handler,font=("Arial",15))
        backButton.grid(row=0,column=0,sticky="w",padx=10,pady=10)

        searchbox = tkinter.Entry(display_top,width=23,font=("Arial",25))
        searchbox.insert(0,query)
        searchbox.grid(row=0,column=1)

        def callback(url,event):
            webbrowser.open_new(url)

        tokenizer = RegexpTokenizer(r'\w+')
        query_list = tokenizer.tokenize(query)
        wordsFiltered = []
        lemmatizer = WordNetLemmatizer()
        stopWords = set(stopwords.words('english'))
        for q in query_list:
            if q not in stopWords:
                wordsFiltered.append(lemmatizer.lemmatize(q.lower()))
        if len(wordsFiltered) == 0:
            for q in query_list:
                wordsFiltered.append(lemmatizer.lemmatize(q.lower()))
    
        shortened_index = {}
        if len(wordsFiltered) > 1:
            shortened_index = efficient_scoring.index_elimination(wordsFiltered, self.index)
            shortened_index = efficient_scoring.contains_many_docs(wordsFiltered, shortened_index)
        elif wordsFiltered[0] in self.index:
            shortened_index.update({wordsFiltered[0]:self.index[wordsFiltered[0]]})
        top_k = efficient_scoring.get_top_k(shortened_index, 10)
        result = []
        for i in range(len(top_k)):
            iurl = self.corpus.file_url_map[top_k[i]]
            url_data = self.fetch_url(iurl)
            soup = BeautifulSoup(url_data['content'],features="lxml")
            desc = "No description could be found"
            try:
                desc = soup.find('title').get_text().strip() + soup.find('p').get_text().strip()
                desc = desc.replace("\n"," ")
                if len(desc) > 100:
                    desc = desc[0:100] + "..."
            except:
                pass
            result.append((tkinter.Label(display_bottom, text = iurl,fg="light blue",bg="gray29",font=("Arial",15)),\
                        tkinter.Label(display_bottom, text = desc,fg="white",bg="gray29",font=("Arial",10))))
            
            result[i][0].grid(row=2*i,padx=10,pady=7,sticky="nw")
            result[i][0].bind("<Button-1>",partial(callback,iurl))
            result[i][1].grid(row=2*i+1,padx=10,sticky="nw")
        class_name = tkinter.Label(otherFrame, text="CS 121 Information Retrieval",\
                                bg = "gray29",fg="white smoke",font=("Arial",12))
        class_name.grid(row=3,pady=10)
        

    def onBack(self, otherFrame):
        """
        Destroying the current display when you want to go
        back to the main search screen
        """
        otherFrame.destroy()
        self.show()
    
    def show(self):
        """
        Shows the main search screen
        """
        self.window.update()
        self.window.deiconify()

    def fetch_url(self,url):
        """
        This method, using the given url, should find the corresponding file in the corpus and return a dictionary
        containing the url, content of the file in binary format and the content size in bytes
        :param url: the url to be fetched
        :return: a dictionary containing the url, content and the size of the content. If the url does not
        exist in the corpus, a dictionary with content set to None and size set to 0 can be returned.
        """
        file_address = self.get_file_name(url)
        if file_address == None: url_data = {"url":url, "content":None}
        file = open(file_address,'rb')
        content = file.read()
        url_data = {"url":url,"content":content}
        return url_data

    def get_file_name(self,url):
        """
        Given a url, this method looks up for a local file in the corpus, and if existed returns file address
        """
        if url in self.corpus.url_file_map:
            addr = self.corpus.url_file_map[url].split("/")
            dir = addr[0]
            file = addr[1]
            return os.path.join(".", "WEBPAGES_RAW", dir, file)
        return None
        
    
if __name__ == "__main__":
    engine = Search_Engine()
    engine.run()
