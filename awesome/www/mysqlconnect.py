# -*- coding: utf-8 -*-
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
        maxsize = kw.get('maxsize',10),
        minsize = kw.get('minsize',1),
        loop = loop
    )

async def select(sql,args,size=None):  #select
    log(sql,args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs = await cur.fetchmany(size) #fetchmany()方法可以获得size条数据
        else:
            rs = await cur.fetchall()   #fetchall()方法获取全部数据
        logging.info('rows returned: %s' % len(rs))
        return rs

#execute中cursor对象不返回结果集，而是通过rowcount返回结果数
async def execute(sql,args,autocommit=True):  #insert,update,delete
    log(sql)
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?','%s'),args)
                affected = cur.rowcount
                if not autocommit:
                    await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affected


