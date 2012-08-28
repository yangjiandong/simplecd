#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pack.py generate html pack
# author: observer
# email: jingchaohu@gmail.com
# blog: http://obmem.com
# last edit @ 2009.12.23
import urllib
import re
import sqlite3
import time
import os,sys
import shutil

path = os.path.dirname(os.path.realpath(sys.argv[0]))
conn = sqlite3.connect(path+'/verycd.sqlite3.db')
conn.text_factory = str

def pack(topath="/tmp/simplecd_htmlpack"):
	try:
		os.mkdir(topath)
	except:
		pass
	shutil.copyfile(path+'/static/main_02.css',topath+'/main_02.css')
	shutil.copyfile(path+'/static/common.js',topath+'/common.js')
	c = conn.cursor()
	c.execute("select verycdid from verycd order by updtime asc")
	ids = c.fetchall()
	baseurl = 'http://www.simplecd.org/?id='
	for id in ids:
		url = baseurl + str(id[0])
		html = urllib.urlopen(url).read()
		html.replace('/static/main_02.css','main_02.css')
		html.replace('/static/common.js','common.js')
		fname = str(id[0])+'.html'
		open(topath+'/'+fname,'w').write(html)
	c.close()

if __name__ == '__main__':
	pack()
