# reallocate.py: vincentg@mltechniques.com
# see step 3 in project 8.2 in Projects4.pdf [download at https://mltblog.com/49w9omx]

import requests

#---[1] Functions to read the input tables (copied from xllm6_util.py)

# map below to deal with some accented / non-standard characters
utf_map = { "&nbsp;"   : " ", 
            "&oacute;" : "o",
            "&eacute;" : "e",
            "&aacute;" : "e",
            "&ouml;"   : "o",
            "&ocirc;"  : "o",
            "&#233;"   : "e",
            "&#243;"   : "o",
            # "&#252;"   : "i",
            "  "       : " ",
            "'s"       : "",   # example: Feller's --> Feller
          }

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


def read_table(filename, type, format = "int", path = ""): 
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


def read_arr_url(filename, path = ""):
    arr_url = []
    data = get_data(filename, path)
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            arr_url.append(line[1])
    return(arr_url)


#---[2] Read the input tables (read locally if paths set to "") 

repository =  "https://raw.githubusercontent.com/VincentGranville/"
# path1 = repository + "Large-Language-Models/main/xllm6/"
# path2 = repository + "Large-Language-Models/main/"
# path3 = repository + "Large-Language-Models/main/xllm6/build-taxonomy/"
path1 = path2 = path3 = ""

arr_url = read_arr_url("xllm6_arr_url.txt", path=path1)
url_map = read_table("xllm6_url_map.txt", type="hash", path=path1)
assignedCategories = read_table("xllm6_assignedCategories.txt", type="list", path=path3)

wolframCategories = {}
data = get_data("list_final_URLs_stats.txt", path2)
for line in data:
    line = line.split('\t')
    url = line[1]
    wcategory = line[2].split(',')
    wcategory = wcategory[0].replace('"','').replace("'","").replace("(","")
    wcategory = wcategory.lower().replace(" ", "~")
    for symbol in utf_map:
        wcategory = wcategory.replace(symbol,utf_map[symbol])
    wolframCategories[url]= wcategory


#---[3] Build hash of detected categories; key = url

url_category_hash = {}  # auxiliary hash table
mode = 'depth'   # options: 'depth' or 'relevancy'

for word in url_map:

    if word in assignedCategories:

        item = assignedCategories[word]
        category = item[0]
        category_level = int(item[1])

        if category_level != 0:  # that is, if a category is assigned to word

            category_relevancy = float(item[2])
            url_hash = url_map[word]  # list or url_IDs that contain word

            for url_ID in url_hash:

                word_count = int(url_hash[url_ID])
                url_ID = int(url_ID)
                if mode == 'relevancy':
                    weight = word_count * category_relevancy
                elif mode == 'depth':
                    weight = word_count * category_level**2
                key = (url_ID, category)
                if key in url_category_hash:
                    url_category_hash[key] += weight
                else: 
                    url_category_hash[key] = weight

detectedCategories = {}

for key in url_category_hash:

    url_ID = key[0]
    url = arr_url[url_ID] 
    category = key[1]
    weight = url_category_hash[key]

    if url in detectedCategories:
        item = detectedCategories[url]
        old_weight = item[1]
        if weight > old_weight: 
            # update detected category assigned to url
            detectedCategories[url] = (category, weight)
    else:
        detectedCategories[url] = (category, weight)


#---[4] Compare Wolfram categories with my content-based reallocation

match = 0
OUT = open("detectedCategories.txt", "w")

for url in detectedCategories:

    print(url)
    item = detectedCategories[url]
    detectedCategory = item[0]
    score = item[1]
    print("Detected category: %s (score = %5.2f)" %(detectedCategory, score))
    print("Wolfram category : %s\n" %(wolframCategories[url]))
    if detectedCategory == wolframCategories[url]:
        match += 1
    OUT.write(url + "\n")
    OUT.write("Detected category: " + detectedCategory + " (score: " + str(score) + ")\n")
    OUT.write("Wolfram  category: " + wolframCategories[url] +"\n\n")


OUT.close()

print("%4d category 'exact match' among %d URLs" %(match, len(wolframCategories))) 
