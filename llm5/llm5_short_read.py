import requests


#--- global variables

pwd = "https://raw.githubusercontent.com/VincentGranville/Large-Language-Models/main/llm5/"

# words can not be any of these words
stopwords = ( "of", "now", "have", "so", "since", "but", "and", 
              "thus", "therefore", "a", "as", "it", "then", "that",
              "with", "to", "is", "will", "the", "if", "there", "then,",
              "such", "or", "for", "be", "where", "on", "at", "in", "can",
              "we", "on", "this", "let", "an", "are", "has", "how", "do",
              "each", "which", "nor", "any", "all", "al.", "by", "having",
              "therefore", "another", "having", "some", "obtaining",
              "into", "does", "union", "few", "makes", "occurs", "were",
              "here", "these", "after", "defined", "takes", "therefore,",
              "here,", "note", "more", "considered", "giving", "obtaining" 
              "etc.", "i.e.,", "Similarly,", "its", "from", "much", "was",
              "given", "Now,", "instead", "above,", "rather", "consider",
              "found", "according", "taking", "proved", "now,", "define",
              "showed", "they", "show", "also", "both", "must", "about",
              "letting", "gives", "their", "otherwise", "called", "descibed",
              "related", "content", "eg", "needed", "picks", "yielding",
              "obtained", "exceed", "until", "complicated", "resulting",
              "give", "write", "directly", "good", "simply", "direction",
              "when", "itself", "ie", "al", "usually", "whose", "being",
              "so-called", "while", "made", "allows", "them", "would", "keeping",
              "denote", "implemented", "his", "shows", "chosen", "just",
              "describes", "way", "stated", "follows", "approaches", "known"
              "result", "sometimes", "corresponds", "every", "referred",
              "produced", "than", "may", "not", "exactly", "&nbsp;", "whether",
              "illustration", ",", ".", "...", "states", "says", "known", "exists",
              "expresses", "respect", "commonly", "describe", "determine", "refer",
              "often", "relies", "used", "especially", "interesting", "versus",
              "consists", "arises", "requires", "apply", "assuming", "said"
            )

# map below to deal with some accented / non-standard characters
utf_map = { "&nbsp;"   : " ", 
            "&oacute;" : "e",
            "&eacute;" : "e",
            "&ouml;"   : "o",
            "&ocirc;"  : "o",
            "&#233;"   : "e",
            "  "       : " ",
            "'s"       : "",   # example: Feller's --> Feller
          }


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


def text_to_list_of_list(string):
    string = string.replace("'","").split('), ')
    list = ()
    for word in string:
        word = word.replace("(","").replace(")","")
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

