import logging
from awesome.www.orm_fa import select,execute

class Field(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' %(self.__class__.__name__,self.column_type,self.name)

class StringField(Field):
    def __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
        super().__init__(name,ddl,primary_key,default)
class BooleanField(Field):
    def __init__(self,name=None,default=False):
        super().__init__(name,'boolean',False,default)
class IntegerField(Field):
    def __init__(self,name=None,primary_key=False,default=0):
        super().__init__(name,'bigint',primary_key,default)
class FloatField(Field):
    def __init__(self,name=None,primary_key=False,default=0.0):
        super().__init__(name,'real',primary_key,default)
class TextField(Field):
    def __init__(self,name=None,default=None):
        super().__init__(name,'text',False,default)
class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)
        tableName = attrs.get('__table__',None) or name
        logging.info('found model: %s (table: %s)' % (name,tableName))
        mappings = dict()
        fields = []
        primaryKey = None
        for k,v in attrs.items():
            if isinstance(v,Field):
                logging.info('found mapping: %s ==> %s ' % (k,v))
                mappings[k] = v
                if v.primary_key:
                    #找到主键
                    if primaryKey:
                        #手动触发异常
                        raise Exception('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise Exception('Primary key not found')
        for k in mappings.keys():
            # pop()方法删除字典给定键key及对应的值，返回值为被删除的值。key值必须给出。 否则，返回default值。
            attrs.pop(k)
        create_args_string,escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings #保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields
        attrs['__select__'] = 'select `%s`,%s from `%s` ' %(primaryKey,','.join(escaped_fields),tableName)
        attrs['__insert__'] = 'insert into ‘%s’ (%s,‘%s’) values (%s)' % (tableName,','.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
        attrs['__update__'] = 'update ’%s‘ set %s where ‘%s‘=?' % (tableName,', '.join(map(lambda f: '’%s‘=?' % (mappings.get(f).name or f),fields)),primaryKey)
        attrs['__delete__'] = 'delete from ’%s‘ where ’%s‘=?' %(tableName,primaryKey)
        return type.__new__(cls,name,bases,attrs)

class Model(dict,metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model, self).__init__(**kw)
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)
    def __setattr__(self, key, value):
        self[key]=value
    def getValue(self,key):
        return getattr(self,key,None)
    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default  #callback是否可调用
                logging.debug('using default value for %s: %s' % (key,str(value)))
                setattr(self,key,value)
        return value

@classmethod #classmethod 修饰符对应的函数不需要实例化，不需要 self 参数，但第一个参数需要是表示自身类的 cls 参数，可以来调用类的属性，类的方法，实例化对象等
async def findAll(cls,where=None,args=None,**kw):
    'find objects by where clause.'
    sql = [cls.__select__]
    if where:
        sql.append('where')
        sql.append(where)
    if args is None:
        args = []
    orderBy = kw.get('orderBy',None)
    if orderBy:
        sql.append('order by')
        sql.append(orderBy)
    limit = kw.get('limit',None)
    if limit is not None:
        sql.append('limit')
        if isinstance(limit,int):
            sql.append('?')
            args.append(limit)
        elif isinstance(limit,tuple) and len(limit) == 2:
            sql.append('?,?')
            args.extend(limit)
        else:
            raise ValueError('Invalid limit value: %s' %str(limit))
        rs = await select(' '.join(sql),args)
        return [cls(**r) for r in rs]

@classmethod
async def findNumber(cls,selectField,where=None,args=None):
    'find number by select and where'
    sql = ['select %s __num__ from `%s`' % (selectField,cls.__table__)]
    if where:
        sql.append('where')
        sql.append(where)
    rs = await select(' '.join(sql),args,1)
    if len(rs) == 0:
        return None
    return rs[0]['__num__']

@classmethod
async def find(cls,pk):
    'find object by primary key'
    rs = await select('%s where `%s`=?' % (cls.__select__,cls.__primary_key__),[pk],1)
    if len(rs) == 0:
        return None
    return cls(**rs[0])

async def save(self):
    args = list(map(self.getValueOrDefault,self.__fields__))
    args.append(self.getValueOrDefault(self.__primary_key__))
    rows = await execute(self.__insert__,args)
    if rows != 1:
        logging.info('failed to insert record: affected rows:%s' % rows)

async def update(self):
    args = list(map(self.getValue,self.__fields__))
    args.append(self.getValue(self.__primary_key__))
    rows = await execute(self.__update__,args)
    if rows != 1:
        logging.info('failed to update by primary key:affected rows: %s' %rows)

async def remove(self):
    args = [self.getValue(self.__primary_key__)]
    rows = await execute(self.__delete__,args)
    if rows != 1:
        logging.info('failed to remove by primaey key: affected rows' % rows)
