# We do import TorRequests class from torpy library
from torpy.http.requests import TorRequests

with TorRequests() as tor_requests:

    # We do a first request to ipify.org with a Tor proxy
    print("build circuit #1")
    with tor_requests.get_session() as sess:
        # use some IP address for crawling
        page1 = sess.get("https://mathworld.wolfram.com/topics/ProbabilityandStatistics.html").text 
        print(page1)
        page2 = sess.get("https://mathworld.wolfram.com/topics/Geometry.html").text
        print(page2)

    # We do a second request to ipify.org with a Tor proxy
    print("build circuit #2")
    with tor_requests.get_session() as sess:
        # switch to some other IP address now
        page3 = sess.get("https://mathworld.wolfram.com/topics/ProbabilityandStatistics.html").text
        print(page3)
