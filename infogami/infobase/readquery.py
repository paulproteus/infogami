import common
from common import all, any
import web

class Query:
    """Query is a list of conditions.
    Each condition is a storage object with ("key", "op", "datatype", "value") as keys.
    
        >>> q = Query()
        >>> q
        <query: []>
        >>> q.add_condition("name", "=", "str", "foo")
        >>> q
        <query: ['name = str:foo']>
        >>> q.add_condition('type', '=', 'ref', '/type/page')
        >>> q.get_type()
        '/type/page'
        >>> q
        <query: ['name = str:foo', 'type = ref:/type/page']>
    """
    def __init__(self, conditions=None):
        self.conditions = conditions or []
        self.sort = None
        self.limit = None
        self.offset = None
        
    def get_type(self):
        """Returns the value of the condition for type if there is any.
        """
        for c in self.conditions:
            #@@ also make sure op is =
            if c.key == 'type':
                return c.value
                
    def assert_type_required(self):
        type_required = any(c.key not in common.COMMON_PROPERTIES for c in self.conditions)
        if type_required and self.get_type() is None:
            raise common.InfobaseException("missing 'type' in query")

    def add_condition(self, key, op, datatype, value):
        self.conditions.append(web.storage(key=key, op=op, datatype=datatype, value=value))
        
    def __repr__(self):
        conditions = ["%s %s %s:%s" % (c.key, c.op, c.datatype, c.value) for c in self.conditions]
        return "<query: %s>" % repr(conditions)

def make_query(store, query):
    """Creates a query object from query dict.
        >>> store = common.create_test_store()
        >>> make_query(store, {'type': '/type/page'})
        <query: ['type = ref:/type/page']>
        >>> make_query(store, {'type': '/type/page', 'title~': 'foo', 'life': 42})
        <query: ['life = int:42', 'type = ref:/type/page', 'title ~ str:foo']>
    """
    q = Query()
    q.offset = query.pop('offset', None)
    q.limit = query.pop('limit', 1000)
    if q.limit > 1000:
        q.limit = 1000
    q.sort = query.pop('sort', None)
    
    for k, v in query.items():
        k, op = parse_key(k)
        q.add_condition(k, op, None, v)
    
    q.assert_type_required()
        
    type = store.get(q.get_type())
    #assert type is not None, 'Not found: ' + q.get_type()
    for c in q.conditions:
        c.datatype = find_datatype(type, c.key, c.value)
    
    return q
    
def find_datatype(type, key, value):
    """
        >>> find_datatype(None, "foo", 1)
        'int'
        >>> find_datatype(None, "foo", True)
        'boolean'
        >>> find_datatype(None, "foo", "hello")
        'str'
    """
    # special properties
    d = dict(
        key="key", 
        type="ref", 
        permission="ref",
        child_permission="ref",
        created="datetime", 
        last_modified="datetime")
        
    if key in d:
        return d[key]
    
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    
    # if possible, get the datatype from the type schema
    p = type and type.get_property(key)
    return (p and common.type2datatype(p.expected_type.key)) or "str"
    
def parse_key(key):
    """Parses key and returns key and operator.
        >>> parse_key('foo')
        ('foo', '=')
        >>> parse_key('foo=')
        ('foo', '=')
        >>> parse_key('foo<')
        ('foo', '<')
        >>> parse_key('foo~')
        ('foo', '~')
    """
    operators = ["=", "!=", "<", "<=", ">=", ">", "~"]
    for op in operators:
        if key.endswith(op):
            key = key[:-len(op)]
            return key, op
    return key, "="
    
def make_versions_query(store, query):
    """Creates a versions query object from query dict.
    """
    q = Query()
    
    q.offset = query.pop('offset', None)
    q.limit = query.pop('limit', 1000)
    if q.limit > 1000:
        q.limit = 1000
    q.sort = query.pop('sort', None)
    
    columns = ['key', 'revision', 'author', 'comment', 'machine_comment', 'ip', 'created']
    
    for k, v in query.items():
        assert k in columns
        q.add_condition(k, '=', None, v)
        
    return q

    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
