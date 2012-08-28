#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# fetchvc.py fetch resources from verycd
#
# author: observer
# email: jingchaohu@gmail.com
# blog: http://obmem.com
# last edit @ 2009.12.23
import urllib
import re
import sqlite3
import time
import os,sys

from threading import Thread
from Queue import Queue

from download import httpfetch

path = os.path.dirname(os.path.realpath(sys.argv[0]))
conn = sqlite3.connect(path+'/verycd.sqlite3.db')
conn.text_factory = str
q = Queue()
MAXC = 8

def thread_fetch():
	conn = sqlite3.connect(path+'/verycd.sqlite3.db')
	conn.text_factory = str
	while True:
		topic = q.get()
		fetch(topic,conn)
		q.task_done()

def search(keyword,full=True):
	'''search verycd, fetch search results'''

	searchlog = path+'/search.log'
	open(searchlog,'a').write('\n'+keyword+'\n')

	url = 'http://www.verycd.com/search/folders/'+keyword
	print 'fetching search results ...'
	res = httpfetch(url)
	topics = re.compile(r'/topics/(\d+)',re.DOTALL).findall(res)
	topics = set(topics)
	links = []
	if full:
		links = re.compile(r'/search/folders/(.*?\?start=\d+)',re.DOTALL).findall(res)
		print links
	print topics
	if topics:
		for topic in topics:
			open(searchlog,'a').write(topic+',')
			q.put(topic)
	if full and links:
		for key in links:
			search(key,full=False)
		

def hot():
	''' read verycd hot res and keep update very day '''
	url = 'http://www.verycd.com/'
	print 'fetching homepage ...'
	home = httpfetch(url)
	hotzone = re.compile(r'热门资源.*?</dl>',re.DOTALL).search(home).group()
	hot = re.compile(r'<a href="/topics/(\d+)/"[^>]*>(《.*?》)[^<]*</a>',re.DOTALL).findall(hotzone)
	html = '<h2 style="color:red">每日热门资源</h2>\n'
	for topic in hot:
		print 'fetching hot topic',topic[0],'...'
		q.put(topic[0])
		html += '&nbsp;<a target="_parent" href="/?id=%s">%s</a>&nbsp;\n' % topic
	open(path+'/static/hot.html','w').write(html)

def normal(pages):
	'''fetch normal res that need login'''
	if '-' in pages:
		(f,t)=[ int(x) for x in pages.split('-') ]
	else:
		f = t = int(pages)
	for page in range(f,t+1):
		url = 'http://www.verycd.com/orz/page%d?stat=normal' % page
		idx = httpfetch(url,needlogin=True)
		ids = re.compile(r'/topics/(\d+)',re.DOTALL).findall(idx)
		print ids[0]
		for id in ids:
			q.put(id)

def request(pages):
	'''fetch request res that need login'''
	if '-' in pages:
		(f,t)=[ int(x) for x in pages.split('-') ]
	else:
		f = t = int(pages)
	for page in range(f,t+1):
		url = 'http://www.verycd.com/orz/page%d?stat=request' % page
		idx = httpfetch(url,needlogin=True)
		ids = re.compile(r'/topics/(\d+)',re.DOTALL).findall(idx)
		print ids[0]
		for id in ids:
			q.put(id)

def feed():
	''' read verycd feed and keep update very 30 min '''
	url = 'http://www.verycd.com/sto/feed'
	print 'fetching feed ...'
	feeds = httpfetch(url)
	ids = re.compile(r'/topics/(\d+)',re.DOTALL).findall(feeds)
	ids = set(ids)
	print ids
	now = time.mktime(time.gmtime())
	for id in ids:
		q.put(id)
		#updtime = fetch(id)
		#updtime = time.mktime(time.strptime(updtime,'%Y/%m/%d %H:%M:%S'))-8*3600 #gmt+8->gmt
		#diff = now - updtime
		#print '%10s secs since update' % (diff)
		#if diff > 1900: # only need recent 30min updates
		#	break

def update(num=10):
	urlbase = 'http://www.verycd.com/sto/~all/page'
	for i in range(1,num+1):
		print 'fetching list',i,'...'		
		url = urlbase+str(i)
		res = httpfetch(url)
		res2 = re.compile(r'"topic-list"(.*?)"pnav"',re.DOTALL).findall(res)
		if res2:
			res2 = res2[0]
		else:
			continue
		topics = re.compile(r'/topics/(\d+)',re.DOTALL).findall(res2)
		topics = set(topics)
		print topics	
		for topic in topics:
			q.put(topic)
		

def fetchall(ran='1-max',debug=False):
	urlbase = 'http://www.verycd.com/archives/'
	if ran == '1-max':
		m1 = 1
		res = urllib.urlopen(urlbase).read()
		m2 = int(re.compile(r'archives/(\d+)').search(res).group(1))
	else:
		m = ran.split('-')
		m1 = int(m[0])
		m2 = int(m[1])
	print 'fetching list from',m1,'to',m2,'...'
	for i in range(m1,m2+1):
		url = urlbase + '%05d'%i + '.html'
		print 'fetching from',url,'...'
		res = httpfetch(url)
		ids = re.compile(r'topics/(\d+)/',re.DOTALL).findall(res)
		print ids
		for id in ids:
			q.put(id)
	

def fetch(id,conn=conn,debug=False):
	print 'fetching topic',id,'...'
	urlbase = 'http://www.verycd.com/topics/'
	url = urlbase + str(id)

	res = ''
	for _ in range(3):
		try:
			res = httpfetch(url,report=True)
			break
		except:
			continue

	abstract = re.compile(r'<h1>.*?visit',re.DOTALL).findall(res)
	if not abstract:
		print res
		if res == '' or '很抱歉' in res:
			print 'resource does not exist'
			return
		else:
			print 'fetching',id,'again...'
			return fetch(id,conn)
	abstract = abstract[0]
    
	title = re.compile(r'<h1>(.*?)</h1>',re.DOTALL).findall(abstract)
	if title:
		title=title[0]
	else:
		return
	try:
		status = re.compile(r'"requestWords">(.*?)<',re.DOTALL).search(abstract).group(1)
		brief = re.compile(r'"font-weight:normal"><span>(.*?)</td>',re.DOTALL).search(abstract).group(1)
		brief = re.compile(r'<.*?>',re.DOTALL).sub('',brief).strip()
		pubtime = re.compile(r'"date-time">(.*?)</span>.*?"date-time">(.*?)</span>',re.DOTALL).findall(abstract)[0]
		category1 = re.compile(r'分类.*?<td>(.*?)&nbsp;&nbsp;(.*?)&nbsp;&nbsp;',re.DOTALL).findall(abstract)[0]
		category = ['','']
		category[0] = re.compile(r'<.*?>',re.DOTALL).sub('',category1[0]).strip()
		category[1] = re.compile(r'<.*?>',re.DOTALL).sub('',category1[1]).strip()
	
#		res2 = re.compile(r'iptcomED2K"><!--eMule.*?<!--eMule end-->',re.DOTALL).findall(res)[0]
	
		ed2k = re.compile(r'ed2k="([^"]*)" (subtitle_[^=]*="[^"]*"[^>]*)>([^<]*)</a>',re.DOTALL).findall(res)
		ed2k.extend( re.compile(r'ed2k="([^"]*)">([^<]*)</a>',re.DOTALL).findall(res) )
	
		content = re.compile(r'<!--eMule end-->(.*?)<!--Wrap-tail end-->',re.DOTALL).findall(res)
	except:
		return

	if content:
		content = content[0]
		content = re.compile(r'<br />',re.DOTALL).sub('\n',content)
		content = re.compile(r'<.*?>',re.DOTALL).sub('',content)
		content = re.compile(r'&.*?;',re.DOTALL).sub(' ',content)
		content = re.compile(r'\n\s+',re.DOTALL).sub('\n',content)
		content = content.strip()
	else:
		content=''

	if debug:
		print title
		print status
		print brief
		print pubtime[0],pubtime[1]
		print category[0],category[1]
		for x in ed2k:
			print x
		print content

	ed2kstr = ''
	for x in ed2k:
		ed2kstr += '`'.join(x)+'`'
	tries=0
	while tries<3:
		try:
			if not dbfind(id,conn):
				dbinsert(id,title,status,brief,pubtime,category,ed2kstr,content,conn)
			else:
				dbupdate(id,title,status,brief,pubtime,category,ed2kstr,content,conn)
			break;
		except:
			tries += 1;
			time.sleep(5);			
			continue;

	return pubtime[1]

def dbcreate():
	c = conn.cursor()
	c.execute('''create table verycd(
		verycdid integer primary key,
		title text,
		status text,
		brief text,
		pubtime text,
		updtime text,
		category1 text,
		category2 text,
		ed2k text,
		content text
	)''')
	conn.commit()
	c.close()

def dbinsert(id,title,status,brief,pubtime,category,ed2k,content,conn):
	c = conn.cursor()
	tries = 0
	while tries<10:
		try:
			c.execute('insert into verycd values(?,?,?,?,?,?,?,?,?,?)',\
				(id,title,status,brief,pubtime[0],pubtime[1],category[0],category[1],\
				ed2k,content))
			break
		except:
			tries += 1
			time.sleep(5)
			continue
	conn.commit()
	c.close()

def dbupdate(id,title,status,brief,pubtime,category,ed2k,content,conn):
	tries = 0
	c = conn.cursor()
	while tries<10:
		try:
			c.execute('update verycd set verycdid=?,title=?,status=?,brief=?,pubtime=?,\
			updtime=?,category1=?,category2=?,ed2k=?,content=? where verycdid=?',\
			(id,title,status,brief,pubtime[0],pubtime[1],category[0],category[1],\
			ed2k,content,id))
			break
		except:
			tries += 1
			time.sleep(5)
			continue
	conn.commit()
	c.close()

def dbfind(id,conn):
	c = conn.cursor()
	c.execute('select 1 from verycd where verycdid=?',(id,))
	c.close()
	for x in c:
		if 1 in x:
			return True
		else:
			return False

def dblist():
	c = conn.cursor()
	c.execute('select * from verycd')
	for x in c:
		for y in x:
			print y

def usage():
	print '''Usage:
  python fetchvc.py createdb
  python fetchvc.py fetchall
  python fetchvc.py fetch 1-1611 #fetch archive list
  python fetchvc.py fetch 5633~5684 #fetch topics
  python fetchvc.py fetch 5633 #fetch a topic
  python fetchvc.py fetch q=keyword
  python fetchvc.py list #list the database
  python fetchvc.py feed #run every 30 min to keep up-to-date
  python fetchvc.py hot
  python fetchvc.py update #update first 20 pages, run on a daily basis'''

#initialize thread pool
for i in range(MAXC):
	t = Thread(target=thread_fetch)
	t.setDaemon(True)
	t.start()

if __name__=='__main__':

	if len(sys.argv) == 1:
		usage()
	elif len(sys.argv) == 2:
		if sys.argv[1] == 'createdb':
			dbcreate()
		elif sys.argv[1] == 'fetchall':
			fetchall()
		elif sys.argv[1] == 'update':
			update(20)
		elif sys.argv[1] == 'update1':
			update(1)
		elif sys.argv[1] == 'feed':
			feed()
		elif sys.argv[1] == 'hot':
			hot()
		elif sys.argv[1] == 'list':
			dblist()
	elif len(sys.argv) == 3:
		if sys.argv[1] != 'fetch':
			usage()
		elif '~' in sys.argv[2]:
			m = sys.argv[2].split('~')
			for i in range(int(m[0]),int(m[1])+1):
				q.put(i)
		elif sys.argv[2].startswith("q="):
			search(sys.argv[2][2:])
		elif sys.argv[2].startswith("n="):
			normal(sys.argv[2][2:])
		elif sys.argv[2].startswith("r="):
			request(sys.argv[2][2:])
		elif '-' in sys.argv[2]:
			fetchall(sys.argv[2])
		else:
			fetch(int(sys.argv[2]),debug=True)

	# wait all threads done
	q.join()
