"""
Philosophy:
    * `struct` is straight, this is of top importance !
      because if you want your struct, compatible with
      several objects, why not define by their intersection ?

    * types in `struct` should be simple, cover bottom basics,
      struct can only be dict: cause most times list needs validation are list contain items of dict.
      structural types   : dict, list
      frank types        : str, unicode, int, bool
      no limitation type : None

    * complex type or custom type is unnesessary,,
      `validators` can handle those things.


struct = {
    'name': str,
    'nature': {
        'luck': int,
        'skill': int,
        'cpow': int,
        'pleasure': int,
        'pain': int,
        'rtrn': int
    },
    'people': [str],
    'disks': [
        {
            'title': str
        }
    ]
}

fmt = [
    '$'
    '$.name'
    '$.nature'
    '$.nature.luck'
    '$.people'
    '$.people.*'
    '$.disks'
    '$.disks.*',
    '$.disks.*.title'
]

data = {
    'name': 'reorx',
    'nature': {
        'luck': 10,
        'skill': 20,
        'cpow': 15,
        'pleasure': 5,
        'pain': 50,
        'rtrn': 100
    },
    'people': [
        'aoyi',
        'utada'
    ],
    'disks': [
        {
            'title': 's',
        },
        {
            'title': 'DATA'
        },
        {
            'title': 'SOURCE'
        }
    ]
}
"""
import logging

DEFAULT_TYPE_VALUE = {
    int: 0,
    float: 0.0,
    str: '',
    unicode: u'', # NOTE think later, this place is dangerous(easy to cause problem) !
    bool: True,
    list: [],
    dict: {},
}

def validate_doc(doc, struct):
    def iter_struct(st, ck):
        #time.sleep(0.3)
        logging.debug('@ ' + ck)
        if isinstance(st, type):
            typ = st
        else:
            typ = type(st)
        logging.debug('define: ' + str(typ))

        # index in doc
        try:
            o = StructedSchema._index_doc(doc, ck)
        except KeyError:
            raise ValidateError(ck + ' could not index out')

        logging.debug('obj: ' + str(o) + str(type(o)))
        if not isinstance(o, tuple):
            o = (o, )
        for i in o:
            logging.debug('item: ' + str(i) + str(type(i)))
            if not isinstance(i, typ):
                raise ValidateError(
                    'invalid {0}, should be {1}'.format(str(type(i)), str(typ)))

        logging.debug('---')
        # iter down step
        if isinstance(st, dict):
            for k, v in st.iteritems():
                nk = ck + '.' + k
                iter_struct(v, nk)
        elif isinstance(st, list):
            nk = ck + '.*'
            iter_struct(st[0], nk)
        else: # isinstance(st, type)
            return
    iter_struct(struct, '$')
    logging.debug('all passed !')

def build_from_struct(struct):
    """
    struct & the result can only be dict

    NOTE list will be passed (build to [])
    """
    def build_dict(dst):
        cd = {}
        for k, v in dst.iteritems():
            if type(v) is dict:
                kv = build_dict(v)
            else:
                if not isinstance(v, type):
                    v = type(v)
                if v in DEFAULT_TYPE_VALUE:
                    kv = DEFAULT_TYPE_VALUE[v]
                else:
                    kv = None
            cd[k] = kv
        return cd
    return build_dict(struct)

class _Gen(object):
    def __init__(self, structObj):
        self.__structObj = structObj
        self.__dot_key = '$'

    def __index_struct(self):
        def recurse_st(st, klist):
            try:
                k = klist.pop(0)
            except:
                return st
            if '*' == k:
                st = st[0]
            else:
                st = st[k]
            return recurse_st(st, klist)
        spKeys = self.__dot_key.split('.')[1:]
        return recurse_st(self.__structObj.struct_main, spKeys)

    def __call__(self):
        struct = self.__index_struct()
        if isinstance(struct, list):
            struct = struct[0]
        # now struct can only be:
        # dict_ins, int*, str*, bool
        if isinstance(struct, dict):
            return build_from_struct(struct)
        else:
            if struct in DEFAULT_TYPE_VALUE:
                return DEFAULT_TYPE_VALUE[struct]
            else:
                return None

    def __getattr__(self, key):
        self.__dot_key = '%s.%s' % (self.__dot_key, key)
        return self


class GenCaller(object):
    def __get__(self, ins, owner):
        return _Gen(owner)

class StructedSchema(object):
    current_struct = None
    gen = GenCaller()
    # TODO rewrite validators ability, has been moved due to multi structs definition
    #validators = {}

    @staticmethod
    def _index_doc(doc, dot_key):
        """
        will raise KeyError if cant index out

        Return:
            1. tuple
            2. non-tuple
        """
        def recurse_doc(d, klist):
            try:
                k = klist.pop(0)
            except:
                return d

            if '*' == k:
                if isinstance(d, list):
                    d = tuple(d)
                elif isinstance(d, tuple):
                    nl = []
                    for i in d:
                        if isinstance(i, list):
                            nl.extend(i)
                        else:
                            nl.append(i)
                    d = tuple(nl)
            elif isinstance(d, tuple):
                nl = []
                for i in d:
                    if isinstance(i, list):
                        for j in i:
                            nl.append(j[k])
                    else:
                        nl.append(i[k])
                d = tuple(nl)
            else:
                d = d[k]
            return recurse_doc(d, klist)

        spKeys = dot_key.split('.')
        spKeys.pop(0)

        return recurse_doc(doc, spKeys)

    # open
    @classmethod
    def validate(cls, doc):
        validate_doc(doc, cls.struct_main)
        print 'done _validate'
        # use validator TODO

    # open
    @classmethod
    def build_instance(cls):
        return build_from_struct(cls.struct_main)

class ValidateError(Exception):
    pass

if '__main__' == __name__:
    # below are test codes
    import unittest

    class TestSchema(StructedSchema):
        struct_main = {
            'name': str,
            'nature': { 'luck': int, },
            'people': [str],
            'disks': [
                {
                    'title': str,
                    'volums': [
                        {
                            'size': int,
                            'block': [int],
                        }
                    ]
                }
            ]
        }
        struct_sub = {
            'hello': str
        }


    class ValidateTestCase(unittest.TestCase):
        def setUp(self):
            self._t_data = {
                'name': 'reorx is the god',
                'nature': { 'luck': 10, },
                'people': [ 'aoyi', ],
                'disks': [
                    {
                        'title': 'My Passport',
                        'volums': [
                            {
                                'size': 1,
                                'block': [12,4,32]
                            }
                        ]
                    },
                    {
                        'title': 'DATA',
                        'volums': [
                            {
                                'size': 2,
                                'block': [1,2,3]
                            }
                        ]
                    }
                ],
                'extra': 'oos'
            }
            self.TS = TestSchema

        def test_base(self):
            self.TS.validate(self._t_data)
            print 'done test_base'


        #def test_ins_main(self):
            #print 'run test 3'
            #ins1 = self.ts.build_instance('main')
            #logging.debug('ins::\n' + str(ins1))

        #def test_ins_sub(self):
            #print 'run test 4'
            #ins2 = self.ts.build_instance('sub')
            #logging.debug('ins::\n' + str(ins2))

    from torext.logger import streamHandler
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(streamHandler)

    unittest.main()
