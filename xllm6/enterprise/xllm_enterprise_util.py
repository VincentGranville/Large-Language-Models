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

    category     = get_value('category', hash_crawl)
    tag_list     = get_value('tag_list', hash_crawl)
    title        = get_value('title', hash_crawl)
    description  = get_value('description', hash_crawl)  #
    meta         = get_value('meta', hash_crawl)
    ID           = get_value('ID', hash_crawl)
    agents       = get_value('agents', hash_crawl)
    full_content = get_value('full_content', hash_crawl) #

    extraWeights = backendParams['extraWeights']
    word = word.lower()  # add stemming
    weight = 1.0  
    flag = ''        
    if word in category:   
        weight += extraWeights['category'] 
        flag = '__'
    if word in tag_list:
        weight += extraWeights['tag_list']
        flag = '__'
    if word in title:
        weight += extraWeights['title']
        flag = '__'
    if word in meta:
        weight += extraWeights['meta']
        flag = '__'

    if flag != '':
        gword = flag + word
        update_nestedHash(backendTables['hash_ID'], gword, ID) 

    update_hash(backendTables['dictionary'], word, weight)
    update_nestedHash(backendTables['hash_context1'], word, category) 
    update_nestedHash(backendTables['hash_context2'], word, tag_list) 
    update_nestedHash(backendTables['hash_context3'], word, title) 
    update_nestedHash(backendTables['hash_context4'], word, description) # takes space, don't build?
    update_nestedHash(backendTables['hash_context5'], word, meta) 
    update_nestedHash(backendTables['hash_ID'], word, ID) 
    update_nestedHash(backendTables['hash_agents'], word, agents) 
    for agent in agents:
         update_nestedHash(backendTables['ID_to_agents'], ID, agent) 
    update_nestedHash(backendTables['full_content'], word, full_content) # takes space, don't nuild?
    update_nestedHash(backendTables['ID_to_content'], ID, full_content)

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
    text = text.replace("'","").replace('"',"").replace('\\n','').replace('!','')
    text = text.replace("\\s",'').replace("\\t",'').replace(","," ").replace(":"," ")  
    text = text.lower() 
    sentence_separators = ('.',)
    for sep in sentence_separators:
        text = text.replace(sep, '_~')
    text = text.split('_~') 

    hash_pairs = backendTables['hash_pairs']
    ctokens = backendTables['ctokens']
    KW_map = backendTables['KW_map']
    stopwords = backendTables['stopwords']
    hwords = {}  # local word hash with word position, to update hash_pairs

    for sentence in text:

        words = sentence.split(" ")
        position = 0
        buffer = []

        for word in words:

            if word in KW_map:     
                # using KW_map (if it exists) results in shorter dictionary
                # for instance, 'products' may be replaced by 'product' in dictionary
                word = KW_map[word] 

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


def cprint(ID, entity): 
    # print text_entity (a JSON text string) nicely

    print("--- Entity %d ---\n" %(ID))
    keys = (
             'title_text', 
             'description_text', 
             'tags_list_text', 
             'category_text', 
             'likes_list_text',
             'link_list_text',
             'Modified Date',
            )
    entity = str(entity).split("~~")
    entity = entity[1].split("{")
    key_value_pairs = get_key_value_pairs(entity)

    for pair in key_value_pairs: 
        if ": " in pair:
            key, value = pair.split(": ", 1)
            key = key.replace("'","")
            if key in keys:
                print("> ",key,":")
                value = value.replace("'",'').split("~")
                for item in value:
                    item = item.lstrip().replace("[","").replace("]","")
                    print(item)
                print()
    return()


def update_params(option, saved_query, sample_queries, frontendParams, backendTables):

    arr = []
    ID_to_content = backendTables['ID_to_content']
    for param in frontendParams:
        arr.append(param)
    task = option
    print()

    if option == '-l':
        print("Multitoken ignore list:\n", frontendParams['ignoreList'])

    elif option == '-v':
        print("%3s %s %s\n" %('Key', 'Description'.ljust(25), 'Value'))
        for key in range(len(arr)):
            param = arr[key]
            value = frontendParams[param]
            if param != 'show':
                print("%3d %s %s" %(key, param.ljust(25), value))
            else:
                print("\nShow sections:\n")
                for section in value:
                    print("    %s %s" %(section.ljust(10),value[section]))

    elif option == '-f':
        # use parameter set to show as much as possible
        for param in frontendParams:
            if param == 'ignoreList':
                frontendParams[param] = ()
            elif param == 'Customized_pmi':
                # use customized pmi
                frontendParams[param] = True
            elif param == 'show':
                showHash = frontendParams[param]
                for section in showHash:
                    # show all sections in output results
                    showHash[section] = True 
            elif param == 'maxTokenCount':
                frontendParams[param] = 999999999
            else:
                frontendParams[param] = 0

    elif option == '-d':
        frontendParams = default_frontendParams()

    elif '-p' in option:
        option = option.split(' ')
        if len(option) == 3:
            paramID = int(option[1])
            if paramID < len(arr):
                param = arr[paramID]
                value = option[2]
                if value == 'True':
                    value = True
                elif value == 'False':
                    value = False
                else:
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

    elif '-i' in option:
        option = option.split(' ')
        nIDs = 0
        for ID in option:
            if ID.isdigit():
                ID = int(ID)
                # print content of text entity ID
                if ID in ID_to_content:
                    cprint(ID, ID_to_content[ID]) 
                    nIDs += 1
        print("\n %d text entities found." % (nIDs))

    elif option == '-s':
        print("Size of some backend tables:")
        print("    dictionary:", len(backendTables['dictionary'])) 
        print("    pairs     :", len(backendTables['hash_pairs'])) 
        print("    ctokens   :", len(backendTables['ctokens']))
        print("    ID_size   :", len(backendTables['ID_size']))

    elif '-c' in option: 
        show = frontendParams['show']
        option = option.split(' ')
        for section in show:
            if section in option or '*' in option:
                show[section] = True
            else:
                show[section] = False

    elif option == '-q':
        print("Saved query:", saved_query)

    elif option == '-x':
        print("Index Query\n")
        for k in range(len(sample_queries)):
            print("  %3d %s" %(k, sample_queries[k]))

    print("\nCompleted task: %s" %(task))
    return(frontendParams)


def print_results(q_dictionary, q_embeddings, backendTables, frontendParams):

    dictionary   = backendTables['dictionary']
    hash_pairs   = backendTables['hash_pairs']
    ctokens      = backendTables['ctokens'] 
    ID_to_agents = backendTables['ID_to_agents']
    ID_size      = backendTables['ID_size']
    show         = frontendParams['show']

    if frontendParams['bypassIgnoreList'] == True:  
        # bypass 'ignore' list
        ignore = ()
    else:
        # ignore multitokens specified in 'ignoreList'
        ignore = frontendParams['ignoreList']  

    if show['Dictionary']: 
        print()
        print(">>> RESULTS - SECTION: q-Dictionary\n")
        for word in q_dictionary:
            print("%5d %s" %(q_dictionary[word], word))
        print()

    if show['Embeddings']:
        # show results from embedding table
        print(">>> RESULTS - SECTION: q-Embeddings\n")  

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
                local_hash[token] = 1 # token marked as displayed, won't be shown again

        print()
        print("N = occurrences of (token, word) in corpus. F = * if contextual pair.")
        print("If no result, try option '-p f'.")
        print()

    sectionLabels = { 
       # map section label to corresponding backend table name
       'Dict' :'dictionary', 
       'Pairs':'hash_pairs', 
       'Category':'hash_context1', 
       'Tags'  :'hash_context2', 
       'Titles':'hash_context3', 
       'Descr.':'hash_context4', 
       'Meta'  :'hash_context5',
       'ID'    :'hash_ID',
       'Agents':'hash_agents',
       'Whole' :'full_content',
    }
    local_hash = {}
    agentAndWord_to_IDs = {}

    for label in show:
        # labels: 'Category','Tags','Titles','Descr.','ID','Whole','Agents','Embeddings'

        if show[label] and label in sectionLabels: 
            # show results for section corresponding to label 

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
                        if label == 'ID' and item in ID_to_agents: 
                            # here item is a text entity ID
                            LocalAgentHash = ID_to_agents[item]
                            local_ID_list = ()
                            for ID in LocalAgentHash:
                                local_ID_list = (*local_ID_list, ID)
                            print("   Agents:", local_ID_list)
                            for agent in local_ID_list: 
                                key3 = (agent, key)  # key is a multitoken
                                update_nestedHash(agentAndWord_to_IDs, key3, item) 

                    print()
            print()

    print("Above results based on words found in prompt, matched back to backend tables.") 
    print("Numbers in parentheses are occurrences of word in corpus.\n") 

    print("--------------------------------------------------------------------")
    print(">>> RESULTS - SECTION: (Agent, Multitoken) --> (ID list)")
    print("    empty unless labels 'ID' and 'Agents' are in 'show'.\n")
    hash_size = {}
    for key in sorted(agentAndWord_to_IDs):
        ID_list = ()
        for ID in agentAndWord_to_IDs[key]:
            ID_list = (*ID_list, ID)
            hash_size[ID] = ID_size[ID]
        print(key,"-->",ID_list)
    print("\n  ID  Size\n")
    for ID in hash_size:
        print("%4d %5d" %(ID, hash_size[ID]))

    return()


def default_frontendParams():

    frontendParams = {
                       'embeddingKeyMinSize': 1, # try 2 
                       'embeddingValuesMinSize': 1,
                       'min_pmi': 0.00,
                       'nABmin': 1,
                       'Customized_pmi': True,
                       'ContextMultitokenMinSize': 1, # try 2
                       'minOutputListSize': 1,
                       'bypassIgnoreList': False,
                       'ignoreList': ('data',),
                       'maxTokenCount': 1000,  # ignore generic tokens if large enough 
                       'beta': 1.0, # used in text entity relevancy score to prompt
                       'show': { 
                                 # names of sections to display in output results
                                 'Embeddings': True,
                                 'Category'  : True, 
                                 'Tags'      : True,
                                 'Titles'    : True,
                                 'Descr.'    : False, # do not built to save space
                                 'Whole'     : False, # do not build to save space
                                 'ID'        : True,
                                 'Agents'    : True,
                                 'Dictionary': True,
                                }
                      }
    return(frontendParams)

# [4.2] Purge function 

def distill_frontendTables(q_dictionary, q_embeddings, frontendParams):
    # purge q_dictionary then q_embeddings (frontend tables) 
    
    maxTokenCount = frontendParams['maxTokenCount']
    local_hash = {}    
    for key in q_dictionary:
        if q_dictionary[key] > maxTokenCount:
            local_hash[key] = 1
    for keyA in q_dictionary:
        for keyB in q_dictionary:
            nA = q_dictionary[keyA]
            nB = q_dictionary[keyB]
            if keyA != keyB:
                if (keyA in keyB and nA == nB) or (keyA in keyB.split('~')):
                    local_hash[keyA] = 1
    for key in local_hash:
        del q_dictionary[key]  

    local_hash = {}    
    for key in q_embeddings: 
        if key[0] not in q_dictionary:
            local_hash[key] = 1
    for key in local_hash:
        del q_embeddings[key] 
  
    return(q_dictionary, q_embeddings)


def create_KW_map(dictionary):
    # singularization
    # map key to KW_map[key], here key is a single token
    # need to map unseen prompt tokens to related dictionary entries 
    #    example: ANOVA -> analysis~variance, ...

    OUT = open("KW_map.txt","w")
    for key in dictionary:
        if key.count('~') == 0: 
            j = len(key)
            keyB = key[0:j-1]
            if keyB in dictionary and key[j-1] == 's':
                if dictionary[key] > dictionary[keyB]:
                    OUT.write(keyB + "\t" + key + "\n")
                else:
                    OUT.write(key + "\t" + keyB + "\n")

    OUT.close()
    return()
