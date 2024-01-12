import numpy as np
import requests
from autocorrect import Speller
from pattern.text.en import singularize
spell = Speller(lang='en')

#--- [1] functions to read core tables (if not produced by you script)

pwd = "https://raw.githubusercontent.com/VincentGranville/Large-Language-Models/main/llm5/"

#--- [1.1] auxiliary functions

def text_to_hash(string, format = "int"): 
    string = string.replace("'","").split(', ')
    hash = {}
    for word in string:
        word = word.replace("{","").replace("}","")
        if word != "":
            word = word.split(": ")
            value = word[1]
            if format == "int":
                value = int(value)
            elif format == "float":
                value = float(value)
            hash[word[0]] = value
    return(hash)


def text_to_list(string):
    if ', ' in string:
        string = string.replace("'","").split(', ')
    else:
        string = string.replace("'","").split(',')
    list = ()
    for word in string:
        word = word.replace("(","").replace(")","")
        if word != "":
            list = (*list, word)
    return(list)


def get_data(filename, path):
    if 'http' in path: 
        response = requests.get(path + filename)
        data = (response.text).replace('\r','').split("\n")
    else:
        file = open(filename, "r")
        data = [line.rstrip() for line in file.readlines()] 
        file.close()
    return(data)


#--- [1.2] functions to read the tables

def read_table(filename, type, format = "int", path = pwd): 
    table = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
          if type == "hash":
              table[line[0]] = text_to_hash(line[1], format)
          elif type == "list": 
              table[line[0]] = text_to_list(line[1])
    return(table)


def read_arr_url(filename, path = pwd):
    arr_url = []
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            arr_url.append(line[1])
    return(arr_url)


def read_stopwords(filename, path = pwd):
    data = get_data(filename, path)
    stopwords = text_to_list(data[0])
    return(stopwords)


def read_dictionary(filename, path = pwd):
    dictionary = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            dictionary[line[0]] = int(line[1]) 
    return(dictionary)


#--- [2] core function to create/update dictionary and satellite tables

def trim(word):
    return(word.replace(".", "").replace(",",""))


def reject(word, stopwords):

    # words can not contain any of these
    # note: "&" and ";" used in utf processing, we keep them 
    flaglist = ( "=", "\"", "(", ")", "<", ">", "}", "|", "&quot;", 
                 "{", "[", "]", "^", "/", "%", ":", "_", 
                )

    # words can not start with any of these chars
    bad_start = ("-",)

    rejected = False
    for string in flaglist:
        if string in word:
            rejected = True
    if len(word) == 0:
        rejected = True
    elif word[0].isdigit() or word[0] in bad_start:
        rejected = True
    if word.lower() in stopwords:
        rejected = True
    return(rejected)


def create_hash(list): 
    hash = {}
    for item in list: 
        if item in hash:
            hash[item] += 1
        elif item != "":
            hash[item] = 1
    return(hash)


def update_hash(word, hash_table, list):
    if list != "":
        hash = hash_table[word]
        for item in list:
            if item in hash:
                hash[item] += 1
            elif item != "":
                hash[item] = 1
        hash_table[word] = hash
    return(hash_table)  


def add_word(word, url_ID, category, dictionary, url_map, hash_category, 
             hash_related, hash_see, related, see, word_pairs, word_list):

    # word is either 1-token, or multiple tokens separated by ~

    urllist = (str(url_ID),) 

    if word in dictionary:

        dictionary[word] += 1
        url_map = update_hash(word, url_map, urllist) 
        hash_category = update_hash(word, hash_category, category) 
        hash_related = update_hash(word, hash_related, related) 
        hash_see = update_hash(word, hash_see, see) 

    else: 

        dictionary[word] = 1 
        urlist = (url_ID,)
        url_map[word] = create_hash(urllist)  
        hash_category[word] = create_hash(category)
        hash_related[word] = create_hash(related)   
        hash_see[word] = create_hash(see)

    # generate association between 2 tokens of a 2-token word 
    # this is the starting point to create word embeddings
 
    if word.count('~') == 1:

        # word consists of 2 tokens word1 and word2
        string = word.split('~')
        word1 = string[0]
        word2 = string[1]

        pair = (word1, word2)
        if pair in word_pairs:
            word_pairs[pair] += 1
        else:
            word_pairs[pair] = 1
        pair = (word2, word1)
        if pair in word_pairs:
            word_pairs[pair] += 1
        else:
            word_pairs[pair] = 1

        if word1 in word_list:
            word_list[word1] = (*word_list[word1], word2)
        else:
            word_list[word1] = (word2,)
        if word2 in word_list:
            word_list[word2] = (*word_list[word2], word1)
        else:
            word_list[word2] = (word1,)

    return()


def stem_data(data, stopwords, dictionary, mode = 'Internal'):

    # input: raw page (array containing the 1-token words)
    # output: words found both in singular and plural: we only keep the former
    # if mode = 'Singularize', use singularize library
    # if mode = 'Internal', use home-made (better)

    stem_table = {}
    temp_dictionary = {}

    for word in data:
        if not reject(word, stopwords):
            trim_word = trim(word)  
            temp_dictionary[trim_word] = 1

    for word in temp_dictionary:
        if mode == 'Internal': 
            n = len(word)
            if n > 2 and "~" not in word and \
                  word[0:n-1] in dictionary and word[n-1] == "s":
                stem_table[word] = word[0:n-1]
            else:
                stem_table[word] = word
        else:
            # the instruction below changes 'hypothesis' to 'hypothesi'
            word = singularize(word)

            # the instruction below changes 'hypothesi' back to 'hypothesis'
            # however it changes 'feller' to 'seller' 
            # solution: create 'do not singularize' and 'do not autocorrect' lists
            stem_table[word] = spell(word) 

    return(stem_table)


def update_core_tables(data, dictionary, url_map, arr_url, hash_category, hash_related, 
                       hash_see, stem_table, category, url, url_ID, stopwords, related, 
                       see, word_pairs, word_list):

    # data is a word array built on crawled data (one webpage, the url)
    # url_ID is incremented at each call of update_core_tables(xx)
    # I/O: dictionary, url_map, word_list, word_pairs, 
    #       hash_see, hash_related, hash_category
    # these tables are updated when calling add_word(xxx)
    
    arr_word = []  # list of words (1 to 4 tokens) found on this page, local array
    k = 0

    for word in data:

        if not reject(word, stopwords):

            raw_word = word
            trim_word = trim(word) 
            trim_word = stem_table[trim_word]

            if not reject(trim_word, stopwords):

                arr_word.append(trim_word)  
                add_word(trim_word, url_ID, category, dictionary, url_map, hash_category, 
                         hash_related, hash_see, related, see, word_pairs, word_list)

                if k > 0 and trim_word == raw_word:
                    # 2-token word
                    if arr_word[k-1] not in trim_word:
                        word = arr_word[k-1] + "~" + trim_word
                        add_word(word, url_ID, category, dictionary, url_map, hash_category, 
                                 hash_related, hash_see, related, see, word_pairs, word_list)

                if k > 1  and trim_word == raw_word:
                    # 3-token word
                    if arr_word[k-2] not in word:
                        word = arr_word[k-2] + "~" + word
                        add_word(word, url_ID, category, dictionary, url_map, hash_category, 
                                 hash_related, hash_see, related, see, word_pairs, word_list)

                if k > 2  and trim_word == raw_word:
                    # 4-token word
                    if arr_word[k-3] not in word:
                        word = arr_word[k-3] + "~" + word      
                        add_word(word, url_ID, category, dictionary, url_map, hash_category, 
                                 hash_related, hash_see, related, see, word_pairs, word_list)
                k += 1

    arr_url.append(url)
    url_ID += 1   
    return(url_ID)


#--- [3] simple text processsing

def collapse_list(list):  
    # group by item and get count for each item
    clist = {}
    for item in list:
        if item in clist:
            clist[item] += 1
        elif item != '': 
            clist[item] = 1
    return(clist)


#--- [4] create embeddings and ngrams tables, once all sources are parsed

def create_pmi_table(word_pairs, dictionary):

    pmi_table  = {}     # pointwise mutual information 
    exponent = 1.0

    for pair in word_pairs:

        word1 = pair[0]
        word2 = pair[1]
        f1 = dictionary[word1] / len(dictionary)
        f2 = dictionary[word2] / len(dictionary)
        f12 = word_pairs[pair] / len(word_pairs) 
        pmi = np.log2(f12 / (f1 * f2)**exponent) 
        word2_weight =  word_pairs[pair] / dictionary[word1]
        pmi_table[pair] = pmi 

    return(pmi_table)


def create_embeddings(word_list, pmi_table): 

    embeddings = {}

    for word in word_list:

        list = word_list[word]
        clist = collapse_list(list)
        embedding_list = {}

        for word2 in clist:
            count = clist[word2] 
            pair =  (word, word2)

            if pair in pmi_table:

                pmi = pmi_table[pair]
                embedding_list[word2] = pmi

        embeddings[word] = embedding_list

    return(embeddings)


def build_ngrams(dictionary):

    ngrams_table = {}
    for word in dictionary:
        tokens = word.split("~")
        tokens.sort()
        sorted_word = tokens[0]
        for k in range(1, len(tokens)):
            sorted_word += "~" + tokens[k] 
        if sorted_word in ngrams_table:
            ngrams_table[sorted_word] = (*ngrams_table[sorted_word], word,)
        else:
            ngrams_table[sorted_word] = (word,) 
    return(ngrams_table)


def compress_ngrams(dictionary, ngrams_table):
    # for each sorted_word, keep most popular ngram only

    compressed_ngrams_table = {}
    for sorted_word in ngrams_table:
        ngrams = ngrams_table[sorted_word]
        max_count = 0
        for ngram in ngrams:
            if dictionary[ngram] > max_count:
                max_count = dictionary[ngram]
                best_ngram = ngram
        compressed_ngrams_table[sorted_word] = (best_ngram, )
    return(compressed_ngrams_table) 


