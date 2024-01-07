import requests

pwd = "https://raw.githubusercontent.com/VincentGranville/Large-Language-Models/main/llm5/"

def read_arr_url(filename, path = pwd, verbose = False):
    if verbose:
        print("Reading arr_url")
    arr_url = []
    response = requests.get(path + filename)
    data = (response.text).replace('\r','').split("\n")
    for line in data:
        line = line.split('\t')
        if len(line) > 1:
            arr_url.append(line[1])
    return(arr_url)