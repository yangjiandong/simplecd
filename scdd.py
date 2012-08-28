#!/usr/bin/env python
#coding: utf-8
#
# scdd.py daemon process
#
# author: observer
# email: jingchaohu@gmail.com
# blog: http://obmem.com
# last edit @ 2009.12.23
import os,sys,time
import re
from daemon import Daemon
import sqlite3
import fetchvc
from download import httpfetch
from Queue import Queue
from threading import Thread
from feed import feed

class MyDaemon(Daemon):
	def __init__(self,path,pid):
		self.path = path
		self.q = Queue()
		Daemon.__init__(self,pid)

	def thread_fetch(self):
		conn = sqlite3.connect(self.path+'/verycd.sqlite3.db')
		conn.text_factory = str
		while True:
			topic = self.q.get()
			if str(topic)=='feed':
				open(self.path+'/static/feed.xml','w').write(feed(self.path,conn))
				self.q.task_done()
				continue
			try:
				fetchvc.fetch(topic,conn)
			except:
				pass
			self.q.task_done()

	def run(self):
		for i in range(8):
			t = Thread(target=self.thread_fetch)
			t.setDaemon(True)
			t.start()

		conn = sqlite3.connect(self.path+'/verycd.sqlite3.db')
		conn.text_factory = str
		while True:
			try:
				#feed
				if time.mktime(time.gmtime())%60<10:
					self.q.put('feed')
				#check searchqueue every 10 secs
				taskqueue = open(self.path+'/searchqueue','r').readlines()
				print taskqueue,time.mktime(time.gmtime()),time.mktime(time.gmtime())%900
				open(self.path+'/searchqueue','w').write('')
				for task in taskqueue:
					url = 'http://www.verycd.com/search/folders/'+task
					print 'fetching', url, '...'
					res = httpfetch(url)
					print '...fetching completed'
					topics = re.compile(r'/topics/(\d+)',re.DOTALL).findall(res)
					topics = set(topics)
					for topic in topics:
						self.q.put(topic)
				if taskqueue == []:
					time.sleep(10)
				# read feed every 900 secs
				if time.mktime(time.gmtime())%600<10:
					url = 'http://www.verycd.com/sto/feed'
					print 'fetching feed ...'
					feeds = httpfetch(url)
					topics = re.compile(r'/topics/(\d+)',re.DOTALL).findall(feeds)
					topics = set(topics)
					print topics
					now = time.mktime(time.gmtime())
					for topic in topics:
						self.q.put(topic)
				# read hot everyday at gmt 19:00
				# read hot every 4 hours
				timeofday =  time.mktime(time.gmtime())%(86400/6)
#				if timeofday>68400 and timeofday < 68410:
				if time.mktime(time.gmtime())%(3600*4)<10:
					url = 'http://www.verycd.com/'
					print 'fetching homepage ...'
					home = httpfetch(url)
					hotzone = re.compile(r'热门资源.*?</dl>',re.DOTALL).search(home).group()
					hot = re.compile(r'<a href="/topics/(\d+)/"[^>]*>(《.*?》)[^<]*</a>',re.DOTALL).findall(hotzone)
					html = '<h2 style="color:red">每日热门资源</h2>\n'
					for topic in hot:
						print 'fetching hot topic',topic[0],'...'
						self.q.put(topic[0])
						html += '&nbsp;<a target="_parent" href="/?id=%s">%s</a>&nbsp;\n' % topic
					open(self.path+'/static/hot.html','w').write(html)
				# update 20 whole pages at gmt 19:10
				if timeofday>69000 and timeofday < 69010:
					urlbase = 'http://www.verycd.com/sto/~all/page'
					for i in range(1,20):
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
							self.q.put(topic)
				# update 1 pages@normal and 1 pages@request every 3600 secs
				if time.mktime(time.gmtime())%3600<10:
					url = 'http://www.verycd.com/orz/page1?stat=normal'
					idx = httpfetch(url,needlogin=True)
					ids = re.compile(r'/topics/(\d+)',re.DOTALL).findall(idx)
					print ids[0]
					for id in ids:
						self.q.put(id)
					url = 'http://www.verycd.com/orz/page1?stat=request'
					idx = httpfetch(url,needlogin=True)
					ids = re.compile(r'/topics/(\d+)',re.DOTALL).findall(idx)
					print ids[0]
					for id in ids:
						self.q.put(id)
			except:
				time.sleep(10)
				continue
			

if __name__ == "__main__":
	path = os.path.dirname(os.path.realpath(sys.argv[0]))
	daemon = MyDaemon(path=path,pid='/tmp/simplevc.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'run' == sys.argv[1]:
			daemon.run()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)
