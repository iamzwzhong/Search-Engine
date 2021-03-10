import pickle
import operator

def index_elimination(query,index):
    """
    Inputted the user's query and the pre-built index and uses that
    to narrow down the index to only postings of high-idf query terms only
    """
    total_urls = len(pickle.load(open('url_set.pkl',"rb")))
    shortened_index = {}
    idf_threshold = 1 #query word is in less than 500 documents
    for word in query:
        if word in index:
            if index[word][1] > idf_threshold and word not in shortened_index:
                shortened_index.update({word:index[word]})
    if len(shortened_index) == 0:
        for word in query:
            if word in index:
                shortened_index.update({word:index[word]})
    return shortened_index

def contains_many_docs(query,index):
    """
    Inputted the user's query and the pre-built index and uses that to
    shorten the postings list to only include documents that contain
    more than one of the query terms
    """
    all_docs = {}
    for word in query:
        if word in index:
            for doc in index[word][0]:
                if doc not in all_docs:
                    all_docs.update({doc:1})
                else:
                    all_docs[doc] += 1
    for word in index:
        for doc in list(index[word][0]):
            if (all_docs[doc]/len(query)) < 0.5:
                index[word][0].pop(doc)
    return index
        
    
            

def qd_scoring(index):
    """
    Takes the shortened index from index_elimination and sums of each documents
    tf-idf. Returns a list of 2-tuples with the first element being the doc_id
    and the second element being the score to that corresponding doc_id.
    """
    scores = {}
    for word in index:
        for docu in index[word][0]:
            if docu in scores:
                scores[docu] += index[word][0][docu][2]
            else:
                scores[docu] = index[word][0][docu][2]
    sorted_scores = sorted(scores.items(), key = operator.itemgetter(1),reverse=True)
    return sorted_scores

def get_top_k(index,k):
    """
    Takes the shortened index from index_elimination and runs it through qd_scoring to
    receive the list which is then shortened down to k number of elements.
    """
    top_k = []
    best = qd_scoring(index)
    if len(best) < k:
        k = len(best)
    for each in range(k):
        top_k.append(best[each][0])
    return top_k
