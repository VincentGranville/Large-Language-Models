import requests
import time
  
# [ToDo] index: https://mathworld.wolfram.com/letters/
# [ToDo] search: https://mathworld.wolfram.com/search/?query=falling+factorial
# [Done] categories: https://mathworld.wolfram.com/topics/
# [ToDo] for final URLs: check "see also" links

URL_list = []
URL_parent_Category = {}
categoryLevel = {}
history = {}
final_URLs = {}

URL_base1 = "https://mathworld.wolfram.com/topics/"  # for directory pages (root)
URL_base2 = "https://mathworld.wolfram.com/"         # for final pages

seed_URL = "https://mathworld.wolfram.com/topics/ProbabilityandStatistics.html"
seed_category = "Probability and Statistics"  # "Root" if starting at URL_base1
categoryLevel[seed_category] = 1  # set to 0 if starting at URL_base1

# seed_URL = "https://mathworld.wolfram.com/topics/"
# seed_category = "Root"  # "Root" if starting at URL_base1
# categoryLevel[seed_category] = 0  # set to 0 if starting at URL_base1

URL_list.append(seed_URL)   # URL stack
URL_parent_Category[seed_URL] = seed_category 

parsed = 0       # number of URLs already parsed
n_URLs = 1       # total number of URLs in the queue 
max_URLs = 5000  # do not crawl more than max_URLs directory pages 

def validate(string):
    Ignore = ['about/','classroom/','contact/','whatsnew/','letters/']
    validated = True  
    if len(string) > 60 or string in Ignore or string.count('topics') > 0:
        validated = False
    return(validated)

def update_lists(new_URL, new_category, parent_category, file):
    URL_parent_Category[new_URL] = new_category
    # if new_category was encountered before, special processing required 
    #   --> in this case, not a one-to-one mapping (ignore here)
    categoryLevel[new_category] = 1 + categoryLevel[parent_category]
    level = str(categoryLevel[new_category])
    file.write(level+"\t"+new_category+"\t"+parent_category+"\n")
    file.flush()
    return()


#---[1] Creating category structure and list of webpages

# file1 allows you to resume from where it stopped in case of crash

file1 = open("crawl_log.txt","w",encoding="utf-8")
file2 = open("crawl_categories.txt","w",encoding="utf-8")

while parsed < min(max_URLs, n_URLs):  

    URL = URL_list[parsed]    # crawl first non-visited URL on the stack
    parent_category = URL_parent_Category[URL]
    level = categoryLevel[parent_category]
    time.sleep(2.5)  #  slow down crawling to avoid being blocked
    parsed += 1

    if URL in history:

        # do not crawl twice the same URL
        print("Duplicate: %s" %(URL)) 
        file1.write(URL+"\tDuplicate\t"+parent_category+"\t"+str(level)+"\n")

    else:   

        print("Parsing: %5d out of %5d: %s" % (parsed, n_URLs, URL))
        # req = requests.get(server, auth=('user',"pass"))
        resp = requests.get(URL, timeout=5)
        history[URL] = resp.status_code

        if resp.status_code != 200:

            print("Failed: %s" %(URL)) 
            file1.write(URL+"\tError:"+str(resp.status_code)+"\t"+parent_category+"\t"+str(level)+"\n")
            file1.flush()

        else: # URL successfully crawled

            file1.write(URL+"\tParsed\t"+parent_category+"\t"+str(level)+"\n")
            page = resp.text
            page = page.replace('\n', ' ')
            page1 = page.split("<a href=\"/topics/")
            page2 = page.split("<a href=\"/")
            n_URLs_old = n_URLs

            # scraping Type-1 page (intermediate directory node) 

            for line in page1:  
                line = line.split("<span>")
                line = line[0]
                if line.count(">") == 1:
                    line = line.split("\">")
                    if len(line) > 1:
                        new_URL = URL_base1 + line[0]
                        new_category = line[1]  
                        URL_list.append(new_URL)
                        update_lists(new_URL, new_category, parent_category, file2)
                        file1.write(new_URL+"\tQueued\t"+new_category+"\t"+str(level+1)+"\n")
                        file1.flush()
                        n_URLs += 1

            # scraping Type-2 page (final directory node)

            if n_URLs == n_URLs_old:

                for line in page2:
                    line = line.split("</a>") 
                    line = line[0].split("\">")
                    if validate(line[0]) and len(line) > 1:
                        new_URL = URL_base2 + line[0]
                        new_category = line[1] 
                        update_lists(new_URL, new_category, parent_category, file2)
                        file1.write(new_URL+"\tEndNode\t"+new_category+"\t"+str(level+1)+"\n")
                        file1.flush()
                        final_URLs[new_URL] = (new_category, parent_category, level+1)

file1.close()
file2.close()

# save list of final URLs to use in step [2]

count = 0
file = open("list_final_URLs.txt","w",encoding="utf-8")
for URL in final_URLs:
    count += 1
    file.write(str(count)+"\t"+URL+"\t"+str(final_URLs[URL])+"\t\n")
file.close()
print()


#---[2] Extracting content from final URLs

# file_log + file_input allows you to resume from where it stopped (in case of crash)

file_input = open("list_final_URLs.txt","r",encoding="utf-8")
file_log = open("crawl_content_log.txt","w",encoding="utf-8")
file_output = open("crawl_final.txt","w",encoding="utf-8")
separator = "\t~"

Lines = file_input.readlines()
file_input.close()
n = len(Lines)      # number of final URLs (final pages)

for line in Lines:

    line = line.split("\t")
    count = int(line[0])
    URL = line[1]
    category = line[2]
    category.replace('\n','')
    print("Page count: %d/%d %s" %(count, n, URL))
 
    resp = requests.get(URL, timeout=5)

    if resp.status_code == 200:
        # add page content: one line per page in the output file
        page = resp.text
        page = page.replace('\n', ' ')
        file_output.write(URL+"\t"+category+separator+page+"\t\n")
        file_output.flush()

    file_log.write(str(count)+"\t"+URL+"\t\n")
    file_log.flush()

file_log.close()
file_output.close()
