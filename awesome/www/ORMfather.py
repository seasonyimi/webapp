import logging
from orm import Model

class Filed(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' %(self.__class__.__name__,self.column_type,self.name)

class StringFiled(Filed):
    def __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
        super().__init__(name,'boolean',False,default)
class BooleanFiled(Filed):
    def __init__(self,name=None,default=False):
        super.__init__(name,'boolean',False,default)
class FloatField(Filed):
    def __init__(self,name=None,primart_key=False,default=0):
        super.__init__(name,'real',primart_key,default)
class ModelMetaclass(type):
    def __new__(cls, name, base, attrs):
        if name == 'Model':
            return type.__new__(cls,name,base,attrs)
        tableName = attrs.get('__table__',None) or name
        logging.info('found model: %s (table: %s)' % (name,tableName))
        mappings = dict()
        fields = []
        primaryKey = None
        for k,v in attrs.items():
            if isinstance(v,Filed):
                logging.info('found mapping: %s ==> %s ' % (k,v))
                mappings[k] = v
                if v.primary_key:
                    #找到主键
                    if primaryKey:
                        pass
