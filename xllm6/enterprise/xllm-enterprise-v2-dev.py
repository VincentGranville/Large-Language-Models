import xllm_enterprise_util as exllm

#--- Backend: create backend tables based on crawled corpus

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
             'located', 'where', 'begins', 'any', 'what', 'some', 'under', 'does', 'belong',
             'included', 'part', 'associated')  
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


#--- Read repository and create all backend tables 

# https://raw.githubusercontent.com/VincentGranville
#    /Large-Language-Models/refs/heads/main/xllm6/enterprise/repository3.txt

IN = open("repository3.txt","r")  
data = IN.read()
IN.close()

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


#-- Create embeddings

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


#-- Create sorted n-grams

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


#--- Functions used to score results ---

def rank(hash):
    # sort hash, then replace values with their rank    

    hash = dict(sorted(hash.items(), key=lambda item: item[1], reverse=True))
    rank = 0
    old_value = 999999999999

    for key in hash:
        value = hash[key]
        if value < old_value:
            rank += 1
        hash[key] = rank
        old_value = value
    return(hash)


def rank_ID(ID_score): 
    # attach weighted relevancy rank to text entity ID, with respect to prompt

    ID_score0 = {}
    ID_score1 = {}
    ID_score2 = {}
    ID_score3 = {}

    for ID in ID_score:
        score = ID_score[ID]    
        ID_score0[ID] = score[0]
        ID_score1[ID] = score[1]
        ID_score2[ID] = score[2]
        ID_score3[ID] = score[3]

    ID_score0 = rank(ID_score0)
    ID_score1 = rank(ID_score1)
    ID_score2 = rank(ID_score2)
    ID_score3 = rank(ID_score3)

    ID_score_ranked = {}
    for ID in ID_score:
        weighted_rank = 2*ID_score0[ID] + ID_score1[ID] + ID_score2[ID] + ID_score3[ID]
        ID_score_ranked[ID] = weighted_rank
    ID_score_ranked = dict(sorted(ID_score_ranked.items(), key=lambda item: item[1]))
    return(ID_score_ranked)


#--- Main: processing prompts ----

print("\n") 
input_ = " "
saved_query = ""
get_bin = lambda x, n: format(x, 'b').zfill(n)
frontendParams = exllm.default_frontendParams() 
beta = 0.5  # overwrite 'beta' frontend param 
ID_to_content = backendTables['ID_to_content']


#--- Main: Read sample prompts with correct answer ---

# https://raw.githubusercontent.com/VincentGranville
#    /Large-Language-Models/refs/heads/main/xllm6/enterprise/enterprise_sample_prompts.txt

IN = open("enterprise_sample_prompts.txt","r") 
prompts = IN.read()
prompts = prompts.split("\n")

# --- Main: Look over all prompts ---

for query in prompts: 

    query = query.split("|")[0]
    print("\n------------------")
    print("Prompt: ", query)
    query = query.replace('?',' ').replace('(',' ').replace(')',' ').replace('.',' ') 
    query = query.replace("'",'').replace("\\s",'')
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
    print("------------------")

    q_embeddings = {} 
    q_dictionary = {} 

    # --- build q_dictionary and q_embeddings based on prompt tokens ---

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
                            # pmi = embedding[token]
                            pmi = exllm.custom_pmi(word, token, backendTables)
                            q_embeddings[(word, token)] = pmi

    # --- Scoring and selecting what to show in prompt results ---

    exllm.distill_frontendTables(q_dictionary,q_embeddings,frontendParams) 
    hash_ID = backendTables['hash_ID']
    ID_hash = {} # local, transposed of hash_ID; key = ID; value = multitoken list

    for word in q_dictionary:
        for ID in hash_ID[word]:
            exllm.update_nestedHash(ID_hash, ID, word, 1) 
        gword = "__" + word  # graph multitoken
        if gword in hash_ID:
            for ID in hash_ID[gword]:
                exllm.update_nestedHash(ID_hash, ID, gword, 1) 

    ID_score = {}
    for ID in ID_hash:
        # score[0] is inverse weighted count
        # score[1] is raw number of tokens found
        score  = [0, 0]  # based on tokens present in the entire text entity
        gscore = [0, 0]  # based on tokens present in graph
        for token in ID_hash[ID]:
            if  token in dictionary:
                score[0] += 1/(q_dictionary[token]**beta)
                score[1] += 1
            else:
                # token must start with "__" (it's a graph token)
                token = token[2:len(token)]
                gscore[0] += 1/(q_dictionary[token]**beta)
                gscore[1] += 1
        ID_score[ID] = [score[0], score[1], gscore[0], gscore[1]]

    # --- Print results ---

    ID_score_ranked = rank_ID(ID_score) 
    n_ID = 0
    print("Most relevant text entities:\n")
    print("\n       ID wRank ID_Tokens")
    for ID in ID_score_ranked:
        if n_ID < 10:
            # context of text entity ID not shown, stored in ID_to_content[ID]
            print("    %5d   %3d %s" %(ID, ID_score_ranked[ID], ID_hash[ID]))        
        n_ID += 1

    print("\nToken count (via dictionary):\n")
    for key in q_dictionary:
        print("    %4d %s" %(q_dictionary[key], key))

    q_embeddings = dict(sorted(q_embeddings.items(), key=lambda item: item[1], reverse=True))
    n_words = 0
    print("\nTop related tokens (via embeddings):\n")
    for word in q_embeddings:
        pmi = q_embeddings[word]
        if n_words < 10: 
            print("    %5.2f %s" %(pmi, word))
        n_words += 1


#--- Save backend tables

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
