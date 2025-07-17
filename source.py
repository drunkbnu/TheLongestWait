from urllib.request import Request, urlopen
import re
from datetime import datetime, timedelta

url = "https://forums.everybodyedits.com/viewtopic.php?id=47849"
selector = "/viewtopic.php?id=47849"
html = ""
r = Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})

#Match next page number in thread.
nextPageRegex = '(?<=<a rel="next" href="viewtopic.php\?id=47849&amp;p=)\d+(?=">Next<\/a>)'

#For matching timestamps.
regexTimeLookBehind = '(?<=<a href="viewtopic.php\?id=47849&p=\d#p\d{6}">' #Positive lookbehind.
regexTimeLookAhead = "(?=<\/a>)" #Positive lookahead.
regexDate = "\d{4}-\d{2}-\d{2}" #YYYY-MM-DD
regexTime = "\d{2}:\d{2}:\d{2}" #HH:MM:SS

#Match YYYY-MM-DD HH:MM:SS of older posts.
regexOlderPostTimestamp = f"{regexTimeLookBehind}){regexDate} {regexTime}{regexTimeLookAhead}"
#Match HH:MM:SS of posts from Yesterday.
regexYesterdayPostTimestamp = f"{regexTimeLookBehind}Yesterday ){regexTime}{regexTimeLookAhead}"
#Match HH:MM:SS of posts from Today.
regexTodayPostTimestamp = f"{regexTimeLookBehind}Today ){regexTime}{regexTimeLookAhead}"

#Match username - one-word or two-word string between ">" and "</span>" AFTER timestamp.
#May not work if username has more than one space.
regexUsername = "(?<=>)\S+( \S+)?(?=<\/span>)"

posts = [] #List of tuples - [(timestamp, author), ...]

while True:
    
    if html != "": #First page already processed.        
        p = re.search(nextPageRegex, html) #Look for next page in thread.
        if p is None: break #No "Next" page. Terminate while loop.
        else: r.selector = f"{selector}&p={p.group()}" #Add next page number to HTML request.
    
    html = urlopen(r).read().decode("utf8") #Download HTML for page.
    
    #Get timestamps and authors of all older posts.
    for match in re.finditer(regexOlderPostTimestamp, html):
        
        #Parse timestamp and convert to unix.
        timestamp = datetime.strptime(match.group(), "%Y-%m-%d %H:%M:%S").timestamp()
        author = re.search(regexUsername, html[match.span()[1]:]).group() #Get post author.
        posts.append((timestamp,  author))
    
    dateToday = datetime.today().date()
    dateYesterday = dateToday - timedelta(days=1)
    
    #Get times and authors of all "Yesterday" posts.
    for match in re.finditer(regexYesterdayPostTimestamp, html):
        
        time = datetime.strptime(match.group(), "%H:%M:%S").time()
        timestamp = datetime.combine(dateYesterday, time).timestamp()
        author = re.search(regexUsername, html[match.span()[1]:]).group()
        posts.append((timestamp,  author))
    
    #Get times and authors of all "Today" posts.
    for match in re.finditer(regexTodayPostTimestamp, html):
        
        time = datetime.strptime(match.group(), "%H:%M:%S").time()
        timestamp = datetime.combine(dateToday, time).timestamp()
        author = re.search(regexUsername, html[match.span()[1]:]).group()
        posts.append((timestamp,  author))

longestDeltas = {} # { "username" = unixDelta, ... }
shortestDeltas = {}

for i in range(1, len(posts)):
    
    name = posts[i][1]
    delta = posts[i][0] - posts[i-1][0]

    #Save longest delta for each poster.
    if name not in longestDeltas or delta > longestDeltas[name]:
        longestDeltas[name] = delta
    
    #Save shortest delta. Ignore doubleposts.
    if (name not in shortestDeltas or delta < shortestDeltas[name]) and name != posts[i-1][1]:
        shortestDeltas[name] = delta
       
print("[b]The Longest Wait:[/b]\n[code]")

#Sort deltas descending and iterate resulting list of tuples.
for i, (name, delta) in enumerate(sorted(longestDeltas.items(), key = lambda x : -x[1])[:10], start=1):
    #Print index (starting at 1), time duration and username.
    s = f"{i}. {str(timedelta(seconds=delta))} - {name}"
    #Pad hours to 2 digits as lazily as possible.
    if s[13] == ":": s = f"{s[:12]}0{s[12:]}"
    print(s)

print("[/code]\n[b]The Shortest Wait:[/b] (Hours:Minutes:Seconds)\n[code]")

for i, (name, delta) in enumerate(sorted(shortestDeltas.items(), key = lambda x : x[1])[:10], start=1):
    #Print index (starting at 1), time duration and username.
    print(f"{i}. {str(timedelta(seconds=delta))} - {name}")
print("[/code]")
