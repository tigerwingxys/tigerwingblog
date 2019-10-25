虎翼博客
====================================

本应用主要实现简单的博客平台，也可以作为简单的私有笔记平台，日志格式为markdown，支持链接feed与链接分享。

源代码：

#1.安装数据库 

参考https://www.postgresql.org安装PostgreSQL。

#2.安装Python支持

本应用需要Python3.5或更高版本，需要插件在requirements.txt中，执行如下命令安装：
`pip -r requirements.txt`

#3.安装Javascript支持

本应用使用了JQuery zTree和Pandao的editormd，以及这两个插件依赖的其他插件，均已经作为项目静态资源使用，如果相关插件有更新，可以替换相关文件即可。
插件详情可参见如下链接，editormd: https://github.com/pandao/editor.md, zTree: http://treejs.cn/

#4.创建postgresql数据库及用户

连接postgresql数据库，`psql -U postgres`

创建用户并赋权:
`   CREATE DATABASE blog;
   CREATE USER blog WITH PASSWORD 'blog';
   GRANT ALL ON DATABASE blog TO blog;`

#5.建立相关库表及函数
` psql -U blog -d blog < schema.sql`


#6.运行

   `./blog.py`

#7.访问虎翼博客

   在浏览器中打开链接http://inmountains.xyz/

