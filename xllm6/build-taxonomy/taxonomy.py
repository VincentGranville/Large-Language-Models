# taxonomy.py: vincentg@mltechniques.com

import requests

# Unlike xllm6.py, xllm6_short.py does not process the (huge) crawled data.
# Instead, it uses the much smaller summary tables produced by xllm6.py


#--- [1] get tables if not present already

# First, get xllm6_util.py from GitHub and save it locally as xllm6_util.py
#     note: this python code does that automatically for  you
# Then import everything from that library with 'from xllm6_util import *'
# Now you can call the read_xxx() functions from that library
# In addition, the tables stopwords and utf_map are also loaded
#
# Notes:
#    - On first use, dowload all locally with overwrite = True
#    - On next uses, please use local copies: set overwrite = False 

# Table description: 
#
# unless otherwise specified, a word consists of 1, 2, 3, or 4 tokens
# word_pairs is used in xllm6.py, not in xllm6_short.py
#
# dictionary = {}      words with counts: core (central) table
# word_pairs = {}      pairs of 1-token words found in same word, with count
# word2_pairs = {}     pairs of multi-token words found on same URL, with count 
# url_map = {}         URL IDs attached to words in dictionary
# arr_url = []         maps URL IDs to URLs (one-to-one)
# hash_category = {}   categories attached to a word
# hash_related = {}    related topics attached to a word
# hash_see = {}        topics from "see also" section, attached to word
# ngrams_table = {}    ngrams of word found when crawling
# compressed_ngrams_table = {}     only keep ngram with highest count
# utf_map = {}         map accented characters to non-accented version
# stopwords = ()       words (1 or more tokens) not accepted in dictionary
# word_hash = {}       list of 1-token words associated to a 1-token word 
# word2_hash = {}      list of multi-token words associated to a multi-token word 
# compressed_word2_hash = {}      shorter version of word2_hash 
# embeddings = {}      key is a 1-token word; value is hash of 1-token:weight
# embeddings2 = {}     key is a word; value is hash of word:weight
  

path = "https://raw.githubusercontent.com/VincentGranville/Large-Language-Models/main/xllm6/"

overwrite = False   # if True, get tables from GitHub, otherwise use local copy

if overwrite:

    response = requests.get(path + "xllm6_util.py")
    python_code = response.text

    local_copy = "xllm6_util"
    file = open(local_copy + ".py", "w")
    file.write(python_code)
    file.close()

    # get local copy of tables

    files = [ 'xllm6_arr_url.txt', 
              'xllm6_compressed_ngrams_table.txt',
              'xllm6_compressed_word2_hash.txt',
              'xllm6_dictionary.txt',
              'xllm6_embeddings.txt',
              'xllm6_embeddings2.txt',
              'xllm6_hash_related.txt',
              'xllm6_hash_category.txt',
              'xllm6_hash_see.txt',
              'xllm6_url_map.txt',
              'xllm6_word2_pairs',
              'stopwords.txt'
            ]

    for name in files:
        response = requests.get(path + name)
        content = response.text
        file = open(name, "w")
        file.write(content)
        file.close()  

import xllm6_util as llm6

# if path argument absent in read_xxx(), read from GitHub
# otherwise, read from copy found in path

arr_url       = llm6.read_arr_url("xllm6_arr_url.txt",       path="")
dictionary    = llm6.read_dictionary("xllm6_dictionary.txt", path="")
stopwords     = llm6.read_stopwords("stopwords.txt",         path="")

compressed_ngrams_table = llm6.read_table("xllm6_compressed_ngrams_table.txt", 
                                                           type="list", path="")
compressed_word2_hash   = llm6.read_table("xllm6_compressed_word2_hash.txt", 
                                                           type="hash", path="")
embeddings    = llm6.read_table("xllm6_embeddings.txt",    type="hash", path="", 
                                                                 format="float") 
embeddings2   = llm6.read_table("xllm6_embeddings2.txt",   type="hash", path="", 
                                                                 format="float") 
hash_related  = llm6.read_table("xllm6_hash_related.txt",  type="hash", path="")
hash_see      = llm6.read_table("xllm6_hash_see.txt",      type="hash", path="")
hash_category = llm6.read_table("xllm6_hash_category.txt", type="hash", path="")
url_map       = llm6.read_table("xllm6_url_map.txt",       type="hash", path="")
word2_pairs   = llm6.read_table("xllm6_word2_pairs.txt",   type="list", path="")


#--- [2] Create/save taxonomy tables if overwrite = True, otherwise read them

from collections import OrderedDict

ignoreWords = { "term", "th", "form", "term", "two", "number", "meaning", "normally", 
                "summarizes", "assumed", "assumes", "p", "s", "et", "possible", 
                "&#9671;", ";", "denoted", "denotes", "computed", "other"}

def create_taxonomy_tables(threshold, thresh2, ignoreWords, dictionary): 

    topWords = {}            # words with highest counts, from dictionary
    wordGroups = {}          # hash of hash: key = topWord; value = hash of words 
                             #        containing topWord (can be empty)
    connectedTopWords = {}   # key = (wordA, wordB) where wordA and wordB contains 
                             #         a topWord; value = occurrences count
    smallDictionary = {}     # dictionary entries (words) containing a topWord
    connectedByTopWord = {}  # same as connectedTopWords, but in flattened hash format; 
                             #         key = topWord
    missingConnections = {}  # if this table is not empty, reduce threshold and/or thresh2

    for word in dictionary:
        n = dictionary[word]     # word count 
        tokens = word.count('~')
        if n > threshold and word not in ignoreWords:    # or tokens > 1 and n > 1: 
            topWords[word] = n  

    for topWord in topWords:
        n1 = dictionary[topWord] 
        hash = {}
        for word in dictionary:
            n2 = dictionary[word]
            if topWord in word and n2 > thresh2 and word != topWord: 
                hash[word] = n2
        if hash:
            hash = dict(sorted(hash.items(), key=lambda item: item[1], reverse=True))
        else: 
            missingConnections[topWord] = 1
        wordGroups[topWord] = hash  

    for topWord in topWords:
        for word in dictionary:
            if topWord in word:
                smallDictionary[word] = dictionary[word]

    counter = 0    
    for topWordA in topWords:
        if counter % 10 == 0:
            print("Create connectedTopWords: ", counter, "/", len(topWords))
        counter += 1
        hash = {}
        for topWordB in topWords:
            key = (topWordA, topWordB)
            if topWordA != topWordB:
                connectedTopWords[key] = 0
                for word in smallDictionary:
                    if topWordA in word and topWordB in word:
                        connectedTopWords[key] += 1
                        if topWordB in hash:
                            hash[topWordB] += 1
                        else:
                            hash[topWordB] = 1
        hash = dict(sorted(hash.items(), key=lambda item: item[1], reverse=True))
        connectedByTopWord[topWordA] = hash

    taxonomy_tables = [topWords, wordGroups, connectedTopWords,
                       smallDictionary, connectedByTopWord, missingConnections]
    return(taxonomy_tables)


def save_taxonomy_tables(): 
   
    list = { "topWords" : topWords,
             "wordGroups" : wordGroups,
             "smallDictionary" : smallDictionary,
             "connectedByTopWord" : connectedByTopWord, 
             "missingConnections" : missingConnections,
           }

    for table_name in list:
        file = open("xllm6_" + table_name + ".txt", "w")
        table = list[table_name]
        for word in table:
            file.write(word + "\t" + str(table[word]) + "\n")
        file.close()

    file = open("xllm6_connectedTopWords.txt", "w") 
    for key in connectedTopWords:
        file.write(str(key) + "\t" + str(connectedTopWords[key]) + "\n")
    file.close()

    return()


#--- Get taxonomy tables 

build_taxonomy_tables = True  # if True, create and save these tables locally (slow)

if build_taxonomy_tables:
 
    threshold = 30     # minimum word count to qualify as topWord 
    thresh2   = 2      # another word count threshold             

    taxonomy_tables    = create_taxonomy_tables(threshold, thresh2, ignoreWords, dictionary)
    topWords           = taxonomy_tables[0] 
    wordGroups         = taxonomy_tables[1] 
    connectedTopWords  = taxonomy_tables[2] 
    smallDictionary    = taxonomy_tables[3] 
    connectedByTopWord = taxonomy_tables[4] 
    missingConnections = taxonomy_tables[5]

    connectedTopWords  = dict(sorted(connectedTopWords.items(), 
                                     key=lambda item: item[1], reverse=True))

    save_taxonomy_tables()
    for topWord in missingConnections:
        print(topWord)
    print()

else:

    smallDictionary     = llm6.read_dictionary("xllm6_smallDictionary.txt", path="")
    topWords            = llm6.read_dictionary("xllm6_topWords.txt", path="")
    wordGroups          = llm6.read_table("xllm6_wordGroups.txt", type="hash", path="")
    connectedByTopWord  = llm6.read_table("xllm6_connectedByTopWord.txt", type="hash", path="")
    
    connectedTopWords = {}
    data = llm6.get_data("xllm6_connectedTopWords.txt", path="")
    for line in data:
        line = line.split('\t')
        count = int(line[1])
        key = llm6.text_to_list(line[0])
        connectedTopWords[key] = count


#--- [3] Play with taxonomy tables to get insights and improve them

topWords = dict(sorted(topWords.items(), key=lambda item: item[0]))

def show_menu(n, dict_mode):

    # option 'o' useful to check if topWordA, topWordB are connected or not
    # option 'c' shows all topWordB connected to topWordA = topWord

    print("Command line menu: \n") 
    print("<Enter>                 - exit")
    print("h                       - help: show menu options")
    print("a                       - show all top words")
    print("ds                      - select short dictionary")
    print("df                      - select full dictionary")
    print("n integer               - display entries with count >= integer")
    print("f string                - find string in dictionary")
    print("g topWord               - print groupWords[topWord]")
    print("c topWord               - print connectedByTopWord[topWord]")
    print("l topWordA topWordB     - (topWordA, topWordB) connections count\n")
    print("current settings: n = %3d, dictionary = %s" %(n, dict_mode))
    print()
    return()

topWords = dict(sorted(topWords.items(), key=lambda item: item[0]))

dict_mode = 'short'
dict  = smallDictionary
query = "o"
n = 0   # return entries with count >= n
show_menu(n, dict_mode)

while query != "":  

    query    = input("Enter command, ex: <c hypothesis> [h for help]: ") 
    queries  = query.split(' ')
    action   = queries[0]
    if len(queries) > 2:
        queries[1] = queries[1] + " " + queries[2]

    if action == 'h':
        show_menu(n, dict_mode)

    elif action == 'ds':
        dict = smallDictionary
        dict_mode = 'short'

    elif action == 'df':
        dict = dictionary
        dict_mode = 'full'

    elif action == 'a':
        for topWord in topWords:
            count = topWords[topWord]
            print(count, topWord)
        print()

    elif action in ('f', 'g', 'c', 'l', 'n') and len(queries) > 1:
        string = queries[1]  

        if action == 'n':
            n = int(string)

        elif action == 'f':
            for word in dict:
                count = dict[word]
                if string in word and count >= n:
                    print(count, string, word)
            print()

        elif action == 'g':
            topWord = string
            if topWord in wordGroups:
                hash = wordGroups[topWord]
                countA = dictionary[topWord]
                for word in hash:
                    countB  = dictionary[word]
                    if countB >= n:
                        print(countA, countB, topWord, word) 
            else:
                print("topWord not in wordGroups")
            print()

        elif action == 'c':
            topWord = string
            if topWord in connectedByTopWord:
                hash = connectedByTopWord[topWord]
                countA = dictionary[topWord]
                for word in hash:
                    countB = dictionary[word]
                    countAB = hash[word]
                    if countAB >= n:
                        print(countA, countB, countAB, topWord, word) 
            else:
                print("topWord not in wordGroups")
            print()

        elif action == 'l':
            astring = string.split(' ')
            if len(astring) == 1:
                print("needs 2 topWords, space-separated")
            else: 
                key = (astring[0], astring[1])
                if key in connectedTopWords:
                    count = connectedTopWords[key]
                else:
                    count = 0
                print(count, key) 

    elif action != '':
        print("Missing arguments")

print()


#--- [4] Build local taxomomy using external taxonomy

## extract categories from external category table... 
## assign category to sample page based on words in page
## stem/plural 

def get_external_taxonomy(hash_category):

    categories = {}
    parent_categories = {}

    for word in hash_category:
        for category_item in hash_category[word]:
            category_item = category_item.lower()
            category_item = category_item.replace('  ',' ').split(' | ')
            category1 = category_item[0].replace(' ', '~')
            category2 = category_item[1].replace(' ', '~')
            level1 = int(category_item[2])
            level2 = level1 - 1
            categories[category1] = level1
            categories[category2] = level2
            parent_categories[category1] = category2
    return(categories, parent_categories)


def compute_similarity(dictionary, word, category):

    tokensA = word.split("~")
    tokensB = category.split("~")
    normA = 0
    normB = 0
    for tokenA in tokensA:
        if tokenA in dictionary:
            normA += dictionary[tokenA]**0.50
    for tokenB in tokensB:
        if tokenB in dictionary:
            normB += dictionary[tokenB]**0.50

    similarity = 0
    for tokenA in tokensA:
        for tokenB in tokensB:
            if tokenA == tokenB and tokenA in dictionary and tokenB in dictionary:
                weight = dictionary[tokenA]
                similarity += weight**0.50
    similarity /= max(normA, normB) 
    return(similarity)

categories, parent_categories = get_external_taxonomy(hash_category)


#--- Main loop

assignedCategories = {}
counter = 0

print("Assign categories to dictionary words\n")

for word in dictionary:
    max_similarity = 0
    max_depth = 0
    NN_category = ""
    for category in categories: 
        depth = categories[category]
        similarity = compute_similarity(dictionary, word, category)
        if similarity > max_similarity:
            max_similarity = similarity
            max_depth = depth
            NN_category = category
    assignedCategories[word] = (NN_category, max_depth, max_similarity)
    if counter % 200 == 0:
        print("%5d / %5d: %d %4.2f %s | %s" 
          %(counter, len(dictionary), max_depth, max_similarity, word, NN_category)) 
    counter += 1

OUT = open("xllm6_assignedCategories.txt", "w")
for word in assignedCategories:
    OUT.write(word+"\t"+str(assignedCategories[word])+"\n")
OUT.close()

