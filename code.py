#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# code.py: based on web.py
#
# author: observer
# email: jingchaohu@gmail.com
# blog: http://obmem.com
# last edit @ 2009.12.23
import os,sys
import web
from web import form
import sqlite3
import fetchvc
import time

web.config.debug = False

path = os.path.dirname(os.path.realpath(sys.argv[0]))

db = web.database(dbn='sqlite', db='f:/verycd.sqlite3.db')#db='verycd.sqlite3.db')
#customdb = web.database(dbn='sqlite',db='custom.sqlite3.db')

conn = sqlite3.connect('custom.sqlite3.db')
conn.text_factory = str

urls = (
	'/', 'index',
	'/add','add',
	'/edit','edit',
	'/del','del',
	'/egg','egg',
)

render = web.template.render('templates/')

vform = form.regexp(r".{3,20}$", '资源密码必须是3-20长度的字符串')
vemail = form.regexp(r".*@.*", "必须提供合法的邮件地址")

add_form = form.Form(
	form.Textbox("email",vemail,description="邮件地址"),
	form.Textbox("password",vform,description="资源密码"),
	form.Textbox("title", description="标题"),
	form.Textbox("brief", description="摘要"),
	form.Dropdown("category1",args=['电影','剧集','音乐','游戏','动漫','综艺','软件','资料'],value="电影",description="分类"),
	form.Textbox("category2",description="子类别"),
	form.Textarea("ed2k",value="[格式]\n文件名#地址\n文件名#地址#字幕地址\n",description="资源链接",cols=60,rows=5),
	form.Textarea("content",description="资源介绍",cols=60,rows=10),
	form.Button("提交", type="submit", description="提交"),
)

app = web.application(urls, globals())

class index:
	def GET(self):
		i = web.input(id=None,page='1',q=None,download=None,qa=None,cat=None)
		hot=open('static/hot.html','r').read()
		#显示单个资源
		if i.id:
			myvar = dict(id=i.id)
			rec = db.select('verycd',vars=myvar,where="verycdid=$id")
			for r in rec:
				fl = None
				if i.download:
					links = r['ed2k'].split('`')
					links = [ x for x in links if 'ed2k:' in x ]
					fl = '<br>\n'.join(links)
				return render.id([r,fl,str(r['verycdid'])])
			return render.error(404)
		#显示最新更新的资源
		else:
			#深度搜索
			if i.qa:
				qa = '+'.join(i.qa.split(' '))
				open(path+'/searchqueue','a').write(qa.encode('utf-8')+'\n')
				return render.fin(qa)
			#默认情况，不指定分类，没有搜索关键字
			elif (not i.q) and (not i.cat):
				vc = db.select('verycd',order='updtime DESC',limit=20,offset=20*(int(i.page)-1))
				num = db.select('verycd',what="count(*) as count")[0].count
				arg = '/?page'
			#无搜索关键字，指定分类
			elif (not i.q) and (i.cat):
				myvar = dict(cat=i.cat)
				vc = db.select('verycd',order='updtime DESC',vars=myvar,where='category1=$cat',limit=20,offset=20*(int(i.page)-1))
				num = db.select('verycd',what="count(*) as count",vars=myvar,where='category1=$cat')[0].count
				arg = '/?cat='+i.cat+'&page'
			#有搜索关键字，指定分类
			elif (i.q) and (i.cat):
				qs = i.q.split(' ')
				qs = [ 'title like \'%'+x+'%\'' for x in qs ]
				where = ' and '.join(qs)
				where += ' and category1=\''+i.cat+'\''
				vc = db.select('verycd',order='updtime DESC',limit=20,\
					offset=20*(int(i.page)-1),where=where)
				num = db.select('verycd',what="count(*) as count",where=where)[0].count
				arg = '/?q='+i.q+'&cat='+i.cat+'&page'
			#有搜索关键字，不指定分类
			else:
				qs = i.q.split(' ')
				qs = [ 'title like \'%'+x+'%\'' for x in qs ]
				where = ' and '.join(qs)
				vc = db.select('verycd',order='updtime DESC',limit=20,\
					offset=20*(int(i.page)-1),where=where)
				num = db.select('verycd',what="count(*) as count",where=where)[0].count
				arg = '/?q='+i.q+'&page'
			prev = int(i.page)-1 == 0 and '1' or str(int(i.page)-1)
			next = int(i.page)+1 <= (num-1)/20+1 and str(int(i.page)+1) or i.page
			end = str((num-1)/20+1)
			pages = [prev,next,end]
			left = min(4,int(i.page)-1)
			right = min(4,int(end)-int(i.page))
			if left < 4:
				right = min(8-left,int(end)-int(i.page))
			if right < 4:
				left = min(8-right,int(i.page)-1)
			while left > 0:
				pages.append(str(int(i.page)-left))
				left -= 1
			j = 0
			while j <= right:
				pages.append(str(int(i.page)+j))
				j += 1
			return render.index([vc,pages,arg,i.q,num,i.cat,hot])

class add:
	def GET(self):
		# do $:f.render() in the template
		f = add_form()
		return render.add(f)

	def POST(self):
		f = add_form()
		if not f.validates():
			return render.add(f)
		else:
			# do whatever is required for registration
			now = time.strftime('%Y/%m/%d %H:%M:%S',time.gmtime(time.time()+3600*8))
			c = conn.cursor()
			c.execute('insert into custom (title,status,brief,pubtime,updtime,\
				category1,category2,ed2k,content) values(?,?,?,?,?,?,?,?,?)',\
				(f.title.get_value(),'新建',f.brief.get_value(),now,now,\
				f.category1.get_value(),f.category2.get_value(),\
				f.ed2k.get_value(),f.content.get_value()))
			c.execute('insert into user (email,password,customid) values (?,?,?)',\
				(f.email.get_value(),f.password.get_value(),c.lastrowid))
			conn.commit()
			c.close()
			return '...'

if __name__ == "__main__":
	# web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
	app.run()
