# xllm5_short.pt : Extreme LLM (light version), vincentg@mltechniques.com

import requests
from autocorrect import Speller
from pattern.text.en import singularize

# Unlike xllm5.py, xllm5_short.py does not process the (huge) crawled data.
# Instead, it uses the much smaller summary tables produced by xllm5.py

#--- [1] get tables if not present already

# First, get xllm5_util.py from GitHub and save it locally as xllm5_util.py
#     note: this python code does that automatically for  you
# Then import everything from that library with 'from xllm5_util import *'
# Now you can call the read_xxx() functions from that library
# In addition, the tables stopwords and utf_map are also loaded
#
# Notes:
#    - On first use, dowload all locally with overwrite = True
#    - On next uses, please use local copies: set overwrite = False 

# Table description: 
#
# unless otherwise specified, a word consists of 1, 2, 3, or 4 tokens
# word_pairs is used in xllm5.py, not in xllm5_short.py
#
# dictionary = {}      words with counts: core (central) table
# word_pairs = {}      pairs of 1-token words found in same word, with count
# url_map = {}         URL IDs attached to words in dictionary
# arr_url = []         maps URL IDs to URLs (one-to-one)
# hash_category = {}   categories attached to a word
# hash_related = {}    related topics attached to a word
# hash_see = {}        topics from "see also" section, attached to word
# word_list = {}       list of 1-token words associated to a 1-token word 
# ngrams_table = {}    ngrams of word found when crawling
# compressed_ngrams_table = {}     only keep ngram with highest count
# utf_map = {}         map accented characters to non-accented version
# stopwords = ()       1-token words not accepted in dictionary

path = "https://raw.githubusercontent.com/VincentGranville/Large-Language-Models/main/llm5/"

overwrite = False

if overwrite:

    response = requests.get(path + "xllm5_util.py")
    python_code = response.text

    local_copy = "xllm5_util"
    file = open(local_copy + ".py", "w")
    file.write(python_code)
    file.close()

    # get local copy of tables

    files = [ 'xllm5_arr_url.txt', 
              'xllm5_compressed_ngrams_table.txt',
              'xllm5_word_list.txt',
              'xllm5_dictionary.txt',
              'xllm5_embeddings.txt',
              'xllm5_hash_related.txt',
              'xllm5_hash_category.txt',
              'xllm5_hash_see.txt',
              'xllm5_url_map.txt',
              'stopwords.txt'
            ]

    for name in files:
        response = requests.get(path + name)
        content = response.text
        file = open(name, "w")
        file.write(content)
        file.close()  

import xllm5_util as llm5

# if path argument absent in read_xxx(), read from GitHub
# otherwise, read from copy found in path

arr_url       = llm5.read_arr_url("xllm5_arr_url.txt",       path="")
dictionary    = llm5.read_dictionary("xllm5_dictionary.txt", path="")
stopwords     = llm5.read_stopwords("stopwords.txt",         path="")

compressed_ngrams_table = llm5.read_table("xllm5_compressed_ngrams_table.txt", 
                                                           type="list", path="")
word_list     = llm5.read_table("xllm5_word_list.txt",     type="list", path="")
embeddings    = llm5.read_table("xllm5_embeddings.txt",    type="hash", path="", 
                                                                 format="float") 
hash_related  = llm5.read_table("xllm5_hash_related.txt",  type="hash", path="")
hash_see      = llm5.read_table("xllm5_hash_see.txt",      type="hash", path="")
hash_category = llm5.read_table("xllm5_hash_category.txt", type="hash", path="")
url_map       = llm5.read_table("xllm5_url_map.txt",       type="hash", path="")


#--- [2] some utilities

def singular(data, mode = 'Internal'):

    stem_table = {}

    for word in data:
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


#--- [3] print some stats (utilities)  

def fformat(value, item, format):
    format = format.split(" ")
    fmt1 = format[0].replace("%","")
    fmt2 = format[1].replace("%","")
    string = '{:{fmt1}} {:{fmt2}}'.format(value,item,fmt1=fmt1,fmt2=fmt2)
    return(string)


def hprint(title, hash, maxprint, output_file, format = "%3d %s"):
    print("\n%s\n" %(title))
    output_file.write("\n%s\n\n" %(title))
    hash_sorted = dict(sorted(hash.items(), 
                        key=lambda item: item[1], reverse=True))
    printcount = 0
    for item in hash_sorted:
        value = hash[item]
        if "URL" in title: 
            item = arr_url[int(item)] 
        if item != "" and printcount < maxprint:
            print(format % (value, item))
            string = fformat(value, item, format)
            output_file.write(string + "\n")
            printcount += 1

    return()


def word_summary(word, ccnt1, ccnt2, maxprint, output_file):  

    if word not in dictionary:
        print("No result")
        output_file.write("No result\n")
        cnt = 0
    else:   
        cnt = dictionary[word]

    if cnt > ccnt1:

        dashes = "-" * 60
        print(dashes)
        output_file.write(dashes + "\n")
        print(word, dictionary[word])
        output_file.write(word + " " + str(dictionary[word]) + "\n")

        hprint("ORGANIC URLs", url_map[word], maxprint, output_file)
        hprint("CATEGORIES & LEVELS", hash_category[word], maxprint, output_file) 
        hprint("RELATED", hash_related[word], maxprint, output_file)
        hprint("ALSO SEE", hash_see[word], maxprint, output_file)

        if word in word_list and word in embeddings:

            # print embedding attached to word

            hash = {}
            weight_list = llm5.collapse_list(word_list[word])
            embedding_list = embeddings[word]

            for word2 in embedding_list:
               if word2 != word:
                   pmi = embedding_list[word2]
                   count = weight_list[word2]
                   product = pmi * count
                   hash[word2] = product 
            
            hprint("EMBEDDINGS", hash, maxprint, output_file, "%8.2f %s")

    print()
    return()


#--- [4] main loop 

dump = False  
 
if dump:

    # hperparameters 
    ccnt1 = 0  # 5
    ccnt2 = 0  # 1
    maxprint = 200  # up to maxprint rows shownn per word/section
    
    dump_file = open("xllm5_dump.txt", "w")
    for word in dictionary:
        word_summary(word, ccnt1, ccnt2, maxprint, dump_file)
    dump_file.close()
     
print("Words (up to 4 tokens):", len(dictionary))
print("1-token words with a list:", len(word_list))
print("1-token words with an embedding:", len(embeddings))


#--- [5] process sample user queries 

def process_query(query, ccnt1, ccnt2, maxprint, output_file = ""):
    # query is a sorted word, each token is in dictionary
    # retrieve all sub-ngrams with a dictionary entry, print results for each one

    get_bin = lambda x, n: format(x, 'b').zfill(n)
    n = len(query)

    for k in range(1, 2**n): 

        binary = get_bin(k, n)
        sorted_word = ""
        for k in range(0, len(binary)):
            if binary[k] == '1':
                if sorted_word == "":
                    sorted_word = query[k]
                else:
                    sorted_word += "~" + query[k]

        if sorted_word in compressed_ngrams_table:
            list = compressed_ngrams_table[sorted_word]
            # the word below (up to 4 tokens) is in the dictionary
            word = list[0]
            print("Found:", word)
            output_file.write("Found:" + word + "\n")
            word_summary(word, ccnt1, ccnt2, maxprint, output_file)

    return()
   

# hyperparameters
ccnt1     = 0  
ccnt2     = 0   # 2  
maxprint = 10  # up to maxprint rows shownn per word/section 

spell = Speller(lang='en')

query = " "
print("\n")
output_file = open("xllm5_results.txt", "w")

while query != "":  

    # entries separated by commas are treated independently
    query = input("Enter queries (ex: Gaussian distribution, central moments): ") 
    queries = query.split(',')
    token_list = []
    token_clean_list = []

    for query in queries:

        tokens = query.split(' ')
        for token in tokens:
            # note: spell('feller') = 'seller', should not be autocorrected
            token = token.lower()
            if token not in dictionary:
                token = spell(token) 
            token_list.append(token)
        stemmed = singular(token_list, mode = 'Internal')   

        for old_token in stemmed:
            token = stemmed[old_token]
            if token in dictionary:
                token_clean_list.append(token)
        token_clean_list.sort()

        if not token_clean_list: 
            if query != "":
                print("No match found")
                output_file.write("No match found\n")
        else:
            print("Found: ", token_clean_list) 
            output_file.write("Found: " + str(token_clean_list) + "\n") 
            process_query(token_clean_list, ccnt1, ccnt2, maxprint, output_file)

output_file.close()
