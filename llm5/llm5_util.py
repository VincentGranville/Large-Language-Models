import requests


#--- global variables

pwd = "https://raw.githubusercontent.com/VincentGranville/Large-Language-Models/main/llm5/"

# map below to deal with some accented / non-standard characters
#utf_map = { "&nbsp;"   : " ", 
#            "&oacute;" : "e",
#            "&eacute;" : "e",
#            "&ouml;"   : "o",
#            "&ocirc;"  : "o",
#            "&#233;"   : "e",
#            "  "       : " ",
#            "'s"       : "",   # example: Feller's --> Feller
#          }


#--- some util functions

def text_to_dictionary(string):
    string = string.replace("'","").split(', ')
    hash = {}
    for word in string:
        word = word.replace("{","").replace("}","")
        if word != "":
            word = word.split(": ")
            hash[word[0]] = float(word[1])
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


def text_to_intlist(string):
    if ', ' in string:
        string = string.replace("'","").split(', ')
    else:
        string = string.replace("'","").split(',')
    list = ()
    for word in string:
        word = word.replace("(","").replace(")","")
        if word != "":
            list = (*list, int(word))
    return(list)


def text_to_list_of_list(string): 
    string = string.replace("\"","").replace("'","").split('), ')
    list = ()
    for word in string:
        word = word.replace("(","").replace(")","").replace("\\","")
        if word != "":
            sublist = text_to_list(word)
            list = (*list, sublist) 
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


#--- functions to read the tables

def read_arr_url(filename, path = pwd):
    arr_url = []
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            arr_url.append(line[1])
    return(arr_url)


def read_url_map(filename, path = pwd):
    url_map = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            url_map[line[0]] = text_to_intlist(line[1])
    return(url_map)


def read_compressed_ngrams_table(filename, path = pwd):
    compressed_ngrams_table = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            compressed_ngrams_table[line[0]] = text_to_list(line[1])
    return(compressed_ngrams_table)


def read_word_list(filename, path = pwd):
    word_list = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            word_list[line[0]] = text_to_list(line[1])
    return(word_list)


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


def read_embeddings(filename, path = pwd):
    embeddings = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            embeddings[line[0]] = text_to_dictionary(line[1])
    return(embeddings)


def read_hash_related(filename, path = pwd):
    hash_related = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            hash_related[line[0]] = text_to_list_of_list(line[1]) 
    return(hash_related)


def read_hash_category(filename, path = pwd):
    hash_category = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            hash_category[line[0]] = text_to_list_of_list(line[1]) 
    return(hash_category)


def read_hash_see(filename, path = pwd):
    hash_see = {}
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            hash_see[line[0]] = text_to_list_of_list(line[1]) 
    return(hash_see)

