#--- [1] Backend: functions

def update_hash(hash, key, count=1):

    if key in hash:
        hash[key] += count
    else:
        hash[key] = count
    return(hash)


def update_nestedHash(hash, key, value, count=1):

    # 'key' is a word here, value is tuple or single value
    if key in hash:
        local_hash = hash[key]
    else:
        local_hash = {}
    if type(value) is not tuple: 
        value = (value,)
    for item in value:
        if item in local_hash:
            local_hash[item] += count
        else:
            local_hash[item] = count
    hash[key] = local_hash
    return(hash)


def get_value(key, hash):
    if key in hash:
        value = hash[key]
    else:
        value = ''
    return(value)


def update_tables(backendTables, word, hash_crawl, backendParams):

    category = get_value('category', hash_crawl)
    tag_list = get_value('tag_list', hash_crawl)
    title    = get_value('title', hash_crawl)
    description =  get_value('description', hash_crawl)
    meta =  get_value('meta', hash_crawl)
    ID   = get_value('ID', hash_crawl)
    full_content = get_value('full_content', hash_crawl)

    extraWeights = backendParams['extraWeights']
    word = word.lower()  # add stemming
    weight = 1.0         
    if word in category:   
        weight += extraWeights['category']
    if word in tag_list:
        weight += extraWeights['tag_list']
    if word in title:
        weight += extraWeights['title']
    if word in meta:
        weight += extraWeights['meta']

    update_hash(backendTables['dictionary'], word, weight)
    update_nestedHash(backendTables['hash_context1'], word, category) 
    update_nestedHash(backendTables['hash_context2'], word, tag_list) 
    update_nestedHash(backendTables['hash_context3'], word, title) 
    update_nestedHash(backendTables['hash_context4'], word, description)
    update_nestedHash(backendTables['hash_context5'], word, meta) 
    update_nestedHash(backendTables['hash_ID'], word, ID) 
    update_nestedHash(backendTables['full_content'], word, full_content) 

    return(backendTables)

 
def clean_list(value):

    # change string "['a', 'b', ...]" to ('a', 'b', ...)
    value = value.replace("[", "").replace("]","")
    aux = value.split("~")
    value_list = ()
    for val in aux:
       val = val.replace("'","").replace('"',"").lstrip()
       if val != '':
           value_list = (*value_list, val)
    return(value_list)


def get_key_value_pairs(entity):

    # extract key-value pairs from 'entity' (a string)
    entity = entity[1].replace("}",", '")
    flag = False
    entity2 = ""

    for idx in range(len(entity)):
        if entity[idx] == '[':
            flag = True
        elif entity[idx] == ']':
            flag = False
        if flag and entity[idx] == ",":
            entity2 += "~"
        else:
            entity2 += entity[idx]

    entity = entity2
    key_value_pairs = entity.split(", '") 
    return(key_value_pairs)


def update_dict(backendTables, hash_crawl, backendParams):

    max_multitoken = backendParams['max_multitoken'] 
    maxDist  =  backendParams['maxDist']     
    maxTerms = backendParams['maxTerms']

    category = get_value('category', hash_crawl)
    tag_list = get_value('tag_list', hash_crawl)
    title = get_value('title', hash_crawl)
    description = get_value('description', hash_crawl)
    meta = get_value('meta', hash_crawl)

    text = category + "." + str(tag_list) + "." + title + "." + description + "." + meta
    text = text.replace('/'," ").replace('(',' ').replace(')',' ').replace('?','')
    text = text.replace("'", "").replace('"',"").replace('\\n','').replace('!','')
    text = text.replace("\\s", '').replace("\\t",'').replace(",", " ")  
    text = text.lower() 
    sentence_separators = ('.',)
    for sep in sentence_separators:
        text = text.replace(sep, '_~')
    text = text.split('_~') 

    hash_pairs = backendTables['hash_pairs']
    ctokens = backendTables['ctokens']
    hwords = {}  # local word hash with word position, to update hash_pairs

    for sentence in text:

        words = sentence.split(" ")
        position = 0
        buffer = []

        for word in words:

            if word not in stopwords: 
                # word is single token
                buffer.append(word)
                key = (word, position)
                update_hash(hwords, key)  # for word correlation table (hash_pairs)
                update_tables(backendTables, word, hash_crawl, backendParams)

                for k in range(1, max_multitoken):
                    if position > k:
                        # word is now multi-token with k+1 tokens
                        word = buffer[position-k] + "~" + word 
                        key = (word, position)
                        update_hash(hwords, key)  # for word correlation table (hash_pairs)
                        update_tables(backendTables, word, hash_crawl, backendParams)

                position +=1     

    for keyA in hwords:
        for keyB in hwords:

            wordA = keyA[0]
            positionA = keyA[1]
            n_termsA = len(wordA.split("~"))

            wordB = keyB[0]
            positionB = keyB[1]
            n_termsB = len(wordB.split("~"))

            key = (wordA, wordB)
            n_termsAB = max(n_termsA, n_termsB)
            distanceAB = abs(positionA - positionB)

            if wordA < wordB and distanceAB <= maxDist and n_termsAB <= maxTerms: 
                  hash_pairs = update_hash(hash_pairs, key) 
                  if distanceAB > 1:
                      ctokens = update_hash(ctokens, key)

    return(backendTables)


#--- [2] Backend: main (create backend tables based on crawled corpus)

tableNames = (
  'dictionary',     # multitokens
  'hash_pairs',     # multitoken associations
  'hash_context1',  # categories
  'hash_context2',  # tags
  'hash_context3',  # titles
  'hash_context4',  # descriptions
  'hash_context5',  # meta
  'ctokens',        # not adjacent pairs in hash_pairs
  'hash_ID',        # ID, such as document ID or url ID
  'full_content'    # full content
)

backendTables = {}
for name in tableNames:
    backendTables[name] = {}

stopwords = ('', '-', 'in', 'the', 'and', 'to', 'of', 'a', 'this', 'for', 'is', 'with', 'from', 
             'as', 'on', 'an', 'that', 'it', 'are', 'within', 'will', 'by', 'or', 'its', 'can', 
             'your', 'be','about', 'used', 'our', 'their', 'you', 'into', 'using', 'these', 
             'which', 'we', 'how', 'see', 'below', 'all', 'use', 'across', 'provide', 'provides',
             'aims', 'one', '&', 'ensuring', 'crucial', 'at', 'various', 'through', 'find', 'ensure',
             'more', 'another', 'but', 'should', 'considered', 'provided', 'must', 'whether',
             'located', 'where', 'begins', 'any')

backendParams = {
    'max_multitoken': 4, # max. consecutive terms per multi-token for inclusion in dictionary
    'maxDist' : 3,       # max. position delta between 2 multitokens to link them in hash_pairs
    'maxTerms': 3,       # maxTerms must be <= max_multitoken
    'extraWeights' :     # deafault weight is 1
       {
          'description': 0.0,
          'category':    0.3,
          'tag_list':    0.4,
          'title':       0.2,
          'meta':        0.1
       }
}


local = True
if local: 
    # get repository from local file
    IN = open("repository.txt","r") 
    data = IN.read()
    IN.close()
else:
    # get repository from GitHub url
    import requests
    url = "https://mltblog.com/3y8MXq5"
    response = requests.get(url)
    data = response.text

entities = data.split("\n")

for entity_raw in entities: 

    entity = entity_raw.split("~~")
    
    if len(entity) > 1: 

        entity_ID = int(entity[0])
        entity = entity[1].split("{")
        hash_crawl = {} 
        hash_crawl['ID'] = entity_ID
        hash_crawl['full_content'] = entity_raw

        key_value_pairs = get_key_value_pairs(entity)

        for pair in key_value_pairs: 
            if ": " in pair:
                key, value = pair.split(": ", 1)
                key = key.replace("'","")
                if key == 'category_text':
                    hash_crawl['category'] = value 
                elif key == 'tags_list_text':
                    hash_crawl['tag_list'] = clean_list(value)
                elif key == 'title_text':
                    hash_crawl['title'] = value
                elif key == 'description_text':
                    hash_crawl['description'] = value
                elif key == 'tower_option_tower':
                    hash_crawl['meta'] = value
        
        backendTables = update_dict(backendTables, hash_crawl, backendParams)


print()
print(len(backendTables['dictionary']))
print(len(backendTables['hash_pairs']))
print(len(backendTables['ctokens']))


# [2.1] Create embeddings

embeddings = {}      # multitoken embeddings based on hash_pairs

hash_pairs = backendTables['hash_pairs']
dictionary = backendTables['dictionary']

for key in hash_pairs:
    wordA = key[0]
    wordB = key[1]
    nA = dictionary[wordA]
    nB = dictionary[wordB]
    nAB = hash_pairs[key]
    pmi = nAB/(nA*nB)**0.5 # try: nAB/(nA + nB - nAB)  
    # if nA + nB  <= nAB: 
    #    print(key, nA, nB, nAB) 
    update_nestedHash(embeddings, wordA, wordB, pmi)
    update_nestedHash(embeddings, wordB, wordA, pmi)


# [2.2] Create sorted n-grams

sorted_ngrams = {}   # to match ngram prompts with embeddings entries

for word in dictionary:
    tokens = word.split('~')
    tokens.sort()
    sorted_ngram = tokens[0]
    for token in tokens[1:len(tokens)]:
        sorted_ngram += "~" + token
    update_nestedHash(sorted_ngrams, sorted_ngram, word)

# print top multitokens
# for key in dictionary:
#    if dictionary[key] > 20:
#        print(key, dictionary[key])


#--- [3] Frontend: functions

# [3.1] custom pmi

def custom_pmi(word, token, backendTables):

    dictionary = backendTables['dictionary']
    hash_pairs = backendTables['hash_pairs']

    nAB = 0
    pmi = 0.00
    keyAB = (word, token)
    if word > token:
        keyAB = (token, word)
    if  keyAB in hash_pairs:
        nAB = hash_pairs[keyAB]
        nA = dictionary[word]
        nB = dictionary[token]
        pmi =  nAB/(nA*nB)**0.5
    return(pmi)

# [3.2] update frontend params

def update_params(option, frontendParams):

    arr = []
    for param in frontendParams:
        arr.append(param)
    print()

    if option == '-l':
        print("Multitoken ignore list:\n", frontendParams['ignoreList'])
    elif option == '-v':
        print("%3s %s %s" %('Key', 'Description'.ljust(25), 'Value'))
        for key in range(len(arr)):
            param = arr[key]
            value = frontendParams[param]
            print("%3d %s %s" %(key, param.ljust(25), value))
    elif option == '-f':
        for param in frontendParams:
            if param == 'ignoreList':
                frontendParams[param] = ()
            else:
                frontendParams[param] = 0
    elif '-p' in option:
        option = option.split(' ')
        if len(option) == 3:
            paramID = int(option[1])
            if paramID < len(arr):
                param = arr[paramID]
                value = float(option[2])
                frontendParams[param] = value
            else:
                print("Error 101: key outside range")
        else:
            print("Error 102: wrong number of arguments")
    elif '-a' in option:
        option = option.split(' ')
        if len(option) == 2:
            ignore = frontendParams['ignoreList']
            ignore =(*ignore, option[1])
            frontendParams['ignoreList'] = ignore
        else:
            print("Error 103: wrong number of arguments")
    elif '-r' in option:
        option = option.split(' ')
        if len(option) == 2:
            ignore2 = ()
            ignore = frontendParams['ignoreList']
            for item in ignore:
                if item != option[1]:
                    ignore2 = (*ignore2, item)
            frontendParams['ignoreList'] = ignore2
        else:
            print("Error 104: wrong number of arguments")
    return(frontendParams)

# [3.3] retrieve info and print results

def print_results(q_dictionary, q_embeddings, backendTables, frontendParams):

    dictionary = backendTables['dictionary']
    hash_pairs = backendTables['hash_pairs']
    ctokens = backendTables['ctokens']  

    if frontendParams['bypassIgnoreList'] == 1:
        # ignore multitokens specified in 'ignoreList'
        ignore = frontendParams['ignoreList']  
    else:
        # bypass 'ignore' list
        ignore = ()

    local_hash = {}  # used to not show same token 2x (linked to 2 different words)     
    q_embeddings = dict(sorted(q_embeddings.items(),key=lambda item: item[1],reverse=True))
    print()
    print("%3s %s %1s %s %s" 
             %('N','pmi'.ljust(4),'F','token [from embeddings]'.ljust(35),
               'word [from prompt]'.ljust(35)))
    print()

    for key in q_embeddings:
        word  = key[0]
        token = key[1]
        pmi = q_embeddings[key]
        ntk1 = len(word.split('~'))
        ntk2 = len(token.split('~'))
        flag = " "
        nAB = 0
        keyAB = (word, token)
        if word > token:
            keyAB = (token, word)
        if  keyAB in hash_pairs:
            nAB = hash_pairs[keyAB]
        if keyAB in ctokens:
            flag = '*'
        if (  ntk1 >= frontendParams['embeddingKeyMinSize'] and 
              ntk2 >= frontendParams['embeddingValuesMinSize'] and
              pmi >= frontendParams['min_pmi'] and 
              nAB >= frontendParams['nABmin'] and
              token not in local_hash and word not in ignore
            ): 
            print("%3d %4.2f %1s %s %s" 
                      %(nAB,pmi,flag,token.ljust(35),word.ljust(35)))
            local_hash[token] = 1 # token marked as displayed, won't be showed again

    print()
    print("N = occurrences of (token, word) in corpus. F = * if contextual pair.")
    print("If no result, try option '-p f'.")
    print()

    sectionLabels = { 
       # map section label (in output) to corresponding backend table name
       'dict' :'dictionary', 
       'pairs':'hash_pairs', 
       'category':'hash_context1', 
       'tags'  :'hash_context2', 
       'titles':'hash_context3', 
       'descr.':'hash_context4', 
       'meta'  :'hash_context5',
       'ID'    :'hash_ID',
       'whole' :'full_content'
    }
    local_hash = {}

    for label in ('category','tags','titles','descr.','ID','whole'):
        tableName = sectionLabels[label]
        table = backendTables[tableName]
        local_hash = {}
        print(">>> RESULTS - SECTION: %s\n" % (label))
        for word in q_dictionary:  
            ntk3 =  len(word.split('~'))
            if word not in ignore and ntk3 >= frontendParams['ContextMultitokenMinSize']: 
                content = table[word]   # content is a hash
                count = int(dictionary[word])
                for item in content:
                    update_nestedHash(local_hash, item, word, count)
        for item in local_hash:
            hash2 = local_hash[item]
            if len(hash2) >= frontendParams['minOutputListSize']:
                print("   %s: %s [%d entries]" % (label, item, len(hash2))) 
                for key in hash2:
                    print("   Linked to: %s (%s)" %(key, hash2[key]))
                print()
        print()

    print()
    print("Results based on words found in prompt, matched back to backend tables.") 
    print("Numbers in parentheses are occurrences of word in corpus.") 

    return()


#--- [4] Frontend: main (process prompt)

print("\n")
input_ = " "
get_bin = lambda x, n: format(x, 'b').zfill(n)

ignore = ('data',)
frontendParams = {
                    'embeddingKeyMinSize': 2,
                    'embeddingValuesMinSize': 2,
                    'min_pmi': 0.00,
                    'nABmin': 1,
                    'Customized_pmi': 1,
                    'ContextMultitokenMinSize': 2,
                    'minOutputListSize': 1,
                    'bypassIgnoreList': 0,
                    'ignoreList': ignore
                  }

sample_queries = (
                    'parameterized datasets map tables sql server',
                    'data load templates importing data database data warehouse',
                    'pipeline extract data eventhub files',
                    'blob storage single parquet file adls gen2',
                    'eventhub files blob storage single parquet',
                    'parquet blob eventhub more files less storage single table',
                    'MLTxQuest Data Assets Detailed Information page'
                    'stellar', 'table',
                 ) 

while len(input_) > 0:  

    print()
    options = ('-p', '-f', '-v', '-a', '-r', '-l')
    print("---")
    print("Query options:")
    print("  -p key value  : set frontendParams['key'] = value")
    print("  -f            : use catch-all parameter set")
    print("  -v            : view parameter set")
    print("  -a multitoken : add multitoken to 'ignore' list")
    print("  -r multitoken : remove multitoken from 'ignore' list")
    print("  -l            : view 'ignore' list")
    print()

    input_ = input("Query, query option, or integer in [0, %d] for sample query: " 
                    %(len(sample_queries)-1))

    flag = True  # False --> query to change params, True --> real query
    for option in options:
        if option in input_:
            update_params(input_, frontendParams)
            input_ = " "
            flag = False
            
    if input_.isdigit(): 
        if int(input_) < len(sample_queries):
           query = sample_queries[int(input_)]
           print("query:",query) 
        else:
           print("Value must be <", len(sample_queries))
           query = ""
    else:
        query = input_

    query = query.split(' ')
    query.sort() 
    q_embeddings = {} 
    q_dictionary = {} 

    for k in range(1, 2**len(query)): 

        binary = get_bin(k, len(query))
        sorted_word = ""
        for k in range(0, len(binary)):
            if binary[k] == '1':
                if sorted_word == "":
                    sorted_word = query[k]
                else:
                    sorted_word += "~" + query[k]

        if sorted_word in sorted_ngrams:
            ngrams = sorted_ngrams[sorted_word]
            for word in ngrams:
                if word in dictionary:
                    q_dictionary[word] = dictionary[word]
                    if word in embeddings:
                        embedding = embeddings[word]
                        for token in embedding:
                            if frontendParams['Customized_pmi'] == 0:
                                pmi = embedding[token]
                            else:
                                # customized pmi
                                pmi = custom_pmi(word, token, backendTables)
                            q_embeddings[(word, token)] = pmi

    if len(query) == 1:
        # single-token query
        frontendParams['embeddingKeyMinSize'] = 1
        frontendParams['ContextMultitokenMinSize'] = 1

    if len(input_) > 0 and flag:
        print_results(q_dictionary, q_embeddings, backendTables, frontendParams)


#--- [5] Save backend tables

save = False
if save:
    for tableName in backendTables:
        table = backendTables[tableName]
        OUT = open('backend_' + tableName + '.txt', "w")
        OUT.write(str(table))
        OUT.close()

    OUT = open('backend_embeddings.txt', "w")
    OUT.write(str(embeddings))
    OUT.close()

    OUT = open('backend_sorted_ngrams.txt', "w")
    OUT.write(str(sorted_ngrams))
    OUT.close()
