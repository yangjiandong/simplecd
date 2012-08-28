#!/usr/bin/env python
# -*- coding: utf-8 -*-
# sample
import urllib,urllib2,cookielib
import re

cookie=cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPHandler)
urllib2.install_opener(opener)

loginform = urllib2.urlopen('http://secure.verycd.com/signin/*/http://www.verycd.com/').read()

#print loginform
fk = re.compile(r'id="fk" value="(.*)"').findall(loginform)[0]
print fk;
postdata=urllib.urlencode({'username':'simcdple',
                           'password':'simcdple',
                           'continueURI':'http://www.verycd.com/',
                           'fk':fk,
                           'login_submit':'登录',
})
req = urllib2.Request(
	url = 'http://secure.verycd.com/signin/*/http://www.verycd.com/',
	data = postdata
)
req.add_header('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6')
req.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
result = urllib2.urlopen(req).read()
#print result
#print result.status
newatt = urllib2.urlopen('http://www.verycd.com/topics/2788317/').read()
print newatt
