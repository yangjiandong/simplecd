https://code.google.com/p/simplecd/wiki/Deployment

3. 简易架设攻略
下载源码

cd /var/www
hg clone https://simplecd.googlecode.com/hg simplecd
cd simplecd
hg update dev-sqlite
注：分支建议采用dev-sqlite，这个和目前网站的代码最为相似

deployment分支继续不变，因为deployment分支代码简单看起来爽一点。

接下来做一些基本的配置

#创建数据库
./fetchvc.py createdb 

#nginx的配置文件(请根据视频进行相应修改)
cp nginx/nginx.conf /etc/nginx/
cp nginx/simplecd /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/simplecd /etc/nginx/sites-enabled/simplecd

#用spawn-fcgi开fcgi
nginx/spawn-fcgi.sh

#开启nginx服务
/etc/init.d/nginx start
