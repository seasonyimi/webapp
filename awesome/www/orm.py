import logging
logging.basicConfig(level=logging.INFO)
import asyncio
import aiomysql #为MYSQL数据库提供了异步IO的驱动

def log(sql, args=()):
    logging.info('SQL: %s' % sql)

async def create_pool(loop,**kw):  #连接数据库信息
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host = kw.get('host','localhost'),
        port = kw.get('port',3306),
        user = kw.get('user','root'),
        password = kw.get('password','season'),
        db = kw.get('db','db1'),
        charset = kw.get('charset','utf8'),
        autocommit = kw.get('autocommit','True'),
        maxsize = kw.get('maxsize','10'),
        minsize = kw.get('minsize','1'),
        loop = loop
    )

async def select(sql,args,size=None):
    log(sql,args)
    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await conn.execute(sql.replace('?','%s'),args or ())

