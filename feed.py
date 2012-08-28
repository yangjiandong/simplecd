#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# feed.py generate rss feed
#
# author: observer
# email: jingchaohu@gmail.com
# blog: http://obmem.com
# last edit @ 2009.12.22
import sqlite3
import time
import os,sys

def feed(path,conn):

	c=conn.cursor()

	for _ in range(10):
		try: 
			c.execute('select * from verycd order by updtime desc limit 20');
			break
		except:
			time.sleep(5)
			continue

	data = None

	try:
		data = c.fetchall()
	except:
		c.close()
		conn.commit()
		return
	
	c.close()
	conn.commit()

	pubdate = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())

	feed = '''<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
<title> SimpleCD - 最新电驴资源 </title>
<atom:link href="http://www.simplecd.org/feed" rel="self" type="application/rss+xml" />
<link>http://www.simplecd.org</link>
<description><![CDATA[ SimpleCD - 最新电驴资源 ]]></description>
<language>zh-cn</language>\n'''
	feed += '<pubDate>%s</pubDate>\n' % pubdate
	feed += '<lastBuildDate>%s</lastBuildDate>\n' % pubdate
	feed += '''<docs>http://blogs.law.harvard.edu/tech/rss</docs>
<generator>SimpleCD.com</generator>
<managingEditor>jingchaohu@gmail.com (webmaster)</managingEditor>
<webMaster>jingchaohu@gmail.com (webmaster)</webMaster>
<ttl>4</ttl>
'''

	for d in data:
		# data:0  1   2      3     4       5       6    7    8    9
		#      id ttl status brief pubtime pudtime cat1 cat2 ed2k content
		title = d[1]
		link = 'http://www.simplecd.org/?id=%s' % d[0]
		rss = '摘要信息：'+d[3]+'<br>\n类别：'+d[6]+'<br>\n子类别：'+d[7]+'<br>\n'
		rss += d[9] 
		feed +='''
	<item>	
		<title><![CDATA[%s]]></title>
		<link>%s</link>
	    <description><![CDATA[
		%s		
		]]>	</description>
		<pubDate>%s</pubDate>
		<dc:creator>observer</dc:creator>
	</item>
'''% (title,link,rss,pubdate)

	feed +='''</channel>
</rss>'''
	return feed

if __name__ == '__main__':
	path = os.path.dirname(os.path.realpath(sys.argv[0]))
	conn = sqlite3.connect(path+'/verycd.sqlite3.db')
	conn.text_factory = str
	print feed(path,conn)
