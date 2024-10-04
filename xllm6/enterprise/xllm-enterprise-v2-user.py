import xllm_enterprise_util as exllm

#--- [2] Backend: main (create backend tables based on crawled corpus)

tableNames = (
  'dictionary',     # multitokens (key = multitoken)
  'hash_pairs',     # multitoken associations (key = pairs of multitokens)
  'ctokens',        # not adjacent pairs in hash_pairs (key = pairs of multitokens)
  'hash_context1',  # categories (key = multitoken)
  'hash_context2',  # tags (key = multitoken)
  'hash_context3',  # titles (key = multitoken)
  'hash_context4',  # descriptions (key = multitoken)
  'hash_context5',  # meta (key = multitoken)
  'hash_ID',        # text entity ID table (key = multitoken, value is list of IDs)
  'hash_agents',    # agents (key = multitoken)
  'full_content',   # full content (key = multitoken)
  'ID_to_content',  # full content attached to text entity ID (key = text entity ID)
  'ID_to_agents',   # map text entity ID to agents list (key = text entity ID)
  'ID_size',        # content size (key = text entity ID)
  'KW_map',         # for singularization, map kw to single-token dictionary entry
  'stopwords',      # stopword list
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
             'located', 'where', 'begins', 'any', 'what', 'some', 'under', 'does', 'belong') 
backendTables['stopwords'] = stopwords

# agent_map works, but hash structure should be improved
# key is word, value is agent (many-to-one). Allow for many-to-many
agent_map = {  
             'template':'Template',
             'policy':'Policy',
             'governance':'Governance',
             'documentation':'Documentation',
             'best practice':'Best Practices',
             'bestpractice':'Best Practices',
             'standard':'Standards',
             'naming':'Naming',
             'glossary':'Glossary',
             'historical data':'Data',
             'overview':'Overview',
             'training':'Training',
             'genai':'GenAI',
             'gen ai':'GenAI',
             'example':'Example',
             'example1':'Example',
             'example2':'Example',
            }

KW_map = {}
save_KW_map = False 
try:
    IN = open("KW_map.txt","r")
except:
    print("KW_map.txt not found on first run: working with empty KW_map.")
    print("KW_map.txt will be created after exiting if save = True.")
    save_KW_map = True 
else: 
    # plural in dictionary replaced by singular form 
    content = IN.read()
    pairs = content.split('\n')
    for pair in pairs: 
        pair = pair.split('\t')
        key = pair[0]
        if len(pair) > 1:
            KW_map[key] = pair[1] 
    IN.close()

# manual additions (plural not in prompt but not dictionary, etc.) 
KW_map['domains'] = 'domain'
KW_map['doing business as'] = 'dba' 

backendTables['KW_map'] = KW_map

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


local = True # first time run, set to False
if local: 
    # get repository from local file
    # https://github.com/VincentGranville/Large-Language-Models/blob/main/xllm6/enterprise/repository.txt
    IN = open("repository.txt","r") 
    data = IN.read()
    IN.close()
else:
    # get anonymized repository from GitHub url
    import requests
    url = "https://mltblog.com/3y8MXq5"
    response = requests.get(url)
    data = response.text

entities = data.split("\n")
ID_size = backendTables['ID_size']

# to avoid duplicate entities (takes space, better to remove them in the corpus)
entity_list = () 

for entity_raw in entities: 

    entity = entity_raw.split("~~")
    agent_list = ()
    
    if len(entity) > 1 and entity[1] not in entity_list: 

        entity_list = (*entity_list, entity[1]) 
        entity_ID = int(entity[0])
        entity = entity[1].split("{")
        hash_crawl = {} 
        hash_crawl['ID'] = entity_ID
        ID_size[entity_ID] = len(entity[1])
        hash_crawl['full_content'] = entity_raw  # do not build to save space

        key_value_pairs = exllm.get_key_value_pairs(entity)

        for pair in key_value_pairs: 

            if ": " in pair:
                key, value = pair.split(": ", 1)
                key = key.replace("'","")
                if key == 'category_text':
                    hash_crawl['category'] = value 
                elif key == 'tags_list_text':
                    hash_crawl['tag_list'] = exllm.clean_list(value)
                elif key == 'title_text':
                    hash_crawl['title'] = value
                elif key == 'description_text':  
                    hash_crawl['description'] = value # do not build to save space
                elif key == 'tower_option_tower':
                    hash_crawl['meta'] = value
                if key in ('category_text','tags_list_text','title_text'):
                    for word in agent_map: 
                        if word in value.lower():
                            agent = agent_map[word]
                            if agent not in agent_list:
                                agent_list =(*agent_list, agent)

        hash_crawl['agents'] = agent_list
        exllm.update_dict(backendTables, hash_crawl, backendParams)


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
    exllm.update_nestedHash(embeddings, wordA, wordB, pmi)
    exllm.update_nestedHash(embeddings, wordB, wordA, pmi)


# [2.2] Create sorted n-grams

sorted_ngrams = {}   # to match ngram prompts with embeddings entries

for word in dictionary:
    tokens = word.split('~')
    tokens.sort()
    sorted_ngram = tokens[0]
    for token in tokens[1:len(tokens)]:
        sorted_ngram += "~" + token
    exllm.update_nestedHash(sorted_ngrams, sorted_ngram, word)

# print top multitokens: useful to build agents, along with sample prompts
# for key in dictionary:
#     if dictionary[key] > 20:
#         print(key, dictionary[key])


# [4.3] Main

print("\n") #
input_ = " "
saved_query = ""
get_bin = lambda x, n: format(x, 'b').zfill(n)
frontendParams = exllm.default_frontendParams()
sample_queries = (
                    'parameterized datasets map tables sql server',
                    'data load templates importing data database data warehouse',
                    'pipeline extract data eventhub files',
                    'blob storage single parquet file adls gen2',
                    'eventhub files blob storage single parquet',
                    'parquet blob eventhub more files less storage single table',
                    'MLTxQuest Data Assets Detailed Information page',
                    'table asset',
                 ) 

while len(input_) > 0:  

    print()
    print("--------------------------------------------------------------------")
    print("Command menu:\n")
    print("  -q             : print last non-command prompt")
    print("  -x             : print sample queries")
    print("  -p key value   : set frontendParams[key] = value")
    print("  -f             : use catch-all parameter set for debugging")
    print("  -d             : use default parameter set")
    print("  -v             : view parameter set")
    print("  -a multitoken  : add multitoken to 'ignore' list")
    print("  -r multitoken  : remove multitoken from 'ignore' list")
    print("  -l             : view 'ignore' list")
    print("  -i ID1 ID2 ... : print content of text entities ID1 ID2 ...")
    print("  -s             : print size of core backend tables")
    print("  -c F1 F2 ...   : show sections F1 F2 ... in output results")
    print("\nTo view available sections for -c command, enter -v command.")
    print("To view available keys for -p command, enter -v command.")
    print("For -i command, choose IDs from list shown in prompt results.")
    print("For standard prompts, enter text not starting with '-' or digit.")
    print("--------------------------------------------------------------------\n")

    input_ = input("Query, command, or integer in [0, %d] for sample query: " 
                    %(len(sample_queries)-1))
    flag = True  # False --> query to change params, True --> real query
    if input_ != "" and input_[0] == '-':
            # query to modify options
            frontendParams = exllm.update_params(input_, saved_query, 
                                                 sample_queries, frontendParams, 
                                                 backendTables)
            query = ""
            flag = False
    elif input_.isdigit(): 
        # actual query (prompt)
        if int(input_) < len(sample_queries):
           query = sample_queries[int(input_)]
           saved_query = query
           print("query:",query) 
        else:
           print("Value must be <", len(sample_queries))
           query = ""
    else:
        # actual query (prompt)
        query = input_
        saved_query = query

    query = query.replace('?',' ').replace('(',' ').replace(')',' ').replace('.',' ')
    query = query.replace("'",'')
    query = query.split(' ')
    new_query = []
    for k in range(len(query)):
        token = query[k].lower()
        if token in KW_map: 
            token = KW_map[token]
        if token in dictionary:
            new_query.append(token)
    query = new_query.copy()
    query.sort() 
    print("Cleaned:", query)
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
                            if not frontendParams['Customized_pmi']: 
                                pmi = embedding[token]
                            else:
                                # customized pmi
                                pmi = exllm.custom_pmi(word, token, backendTables)
                            q_embeddings[(word, token)] = pmi

    # if len(query) == 1: 
    #     # single-token query
    #     frontendParams['embeddingKeyMinSize'] = 1
    #     frontendParams['ContextMultitokenMinSize'] = 1

    exllm.distill_frontendTables(q_dictionary,q_embeddings,frontendParams)

    if len(input_) > 0 and flag: 
        exllm.print_results(q_dictionary, q_embeddings, backendTables, frontendParams) 


#--- [5] Save backend tables

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

if save_KW_map:
    # save it only if it does not exist
    create_KW_map(dictionary)  

save = True 
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
