from urllib import request as urlrequest
import random

username = 'your_username'
password = 'your_password'
port = 22225
session_id = random.random()
super_proxy_url = ('http://%s-country-us-session-%s:%s@brd.superproxy.io:%d' %
        (username, session_id, password, port))
proxy_handler = urlrequest.ProxyHandler({
        'http': super_proxy_url,
        'https': super_proxy_url,
    })

opener = urlrequest.build_opener(proxy_handler)
print('Performing request') 

URL = 'https://mathworld.wolfram.com/topics/FoundationsofMathematics.html'

response = opener.open(URL)
status_code = response.getcode()  
page = response.read()
print(page)
print("status code: ", status_code)

# check which IP was used for crawling

URL = "https://ipecho.net/plain"
response = opener.open(URL)
print(response.read())
