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

class ValidateError(Exception):
    pass


class StructedSchema(object):
    current_struct = None
    # TODO rewrite validators ability, has been moved due to multi structs definition
    #validators = {}

    @staticmethod
    def _index_doc(doc, dot_key):
        """
        will raise KeyError if cant index out
        """
        def recurse_doc(d, klist):
            try:
                k = klist.pop(0)
            except:
                return d

            if '*' == k:
                d = d[0]
            else:
                d = d[k]
            return recurse_doc(d, klist)

        spKeys = dot_key.split('.')
        spKeys.pop(0)

        return recurse_doc(doc, spKeys)

    @staticmethod
    def _validate(doc, struct):
        def iter_struct(st, ck):

            if isinstance(st, type):
                typ = st
            else:
                typ = type(st)
            logging.debug('@ {0}, {1}'.format(ck, str(typ)))
            # indexing in doc
            try:
                o = StructedSchema._index_doc(doc, ck)
            except (KeyError, IndexError):
                raise ValidateError(ck + ' cant be indexed')
            logging.debug('obj: {0} {1}'.format(str(o), str(type(o) ) ) )

            # check o type
            if not isinstance(o, typ):
                raise ValidateError(
                    '{0} type {1} invalid, should be: {2}'.format(ck, type(o), typ))
            logging.debug('check pass\n')

            # check if extra validator
            # TODO validator checking
#                validator = self.validators.get(ck)
#                if validator:
#                    try:
#                        ro = validator(o)
#                    except Exception, e:
#                        raise ValidateError(str(e))
#                    if isinstance(ro, str):
#                        raise ValidateError(ro)
#                    if ro is False:
#                        raise ValidateError('validator unpassed: ' + ck)

            # iter down step
            if isinstance(st, dict):
                for k, v in st.iteritems():
                    nk = ck + '.' + k
                    iter_struct(v, nk)
            elif isinstance(st, list):
                for i in st:
                    nk = ck + '.*'
                    iter_struct(i, nk)
            else: # isinstance(st, type)
                return

        # start iterd function
        iter_struct(struct, '$')

        # no error means all passed !
        logging.info('doc validate all passed !')
        return True

    @classmethod
    def validate(cls, doc, name='main'):
        try:
            struct = getattr(cls, 'struct_' + name)
        except AttributeError:
            raise AttributeError('No corresponding struct defined')
        cls._validate(doc, struct)

    @classmethod
    def build_instance(cls, name):
        """
        instance can only be dict

        TODO instance can check input value type
        """
        struct = getattr(cls, 'struct_' + name)

        def build_dict(dst):
            cd = {}
            for k, v in dst.iteritems():
                if v is dict:
                    cd[k] = {}
                elif type(v) is dict:
                    cd[k] = build_dict(v)
                elif v is list or type(v) is list:
                    cd[k] = []
                else:
                    cd[k] = None
            return cd

        return build_dict(struct)

if '__main__' == __name__:
    # below are test codes
    import unittest

    class TestSchema(StructedSchema):
        struct_main = {
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
        struct_sub = {
            'hello': str
        }


    class ValidateTestCase(unittest.TestCase):
        def setUp(self):
            self._t_data = {
                'name': 'reorx is the god',
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
                        'title': 'My Passport',
                    },
                    {
                        'title': 'DATA'
                    },
                    {
                        'title': 'SOURCE'
                    }
                ]
            }
            self.TS = TestSchema

        def test_base(self):
            self.TS.validate(self._t_data)

        def test_sub(self):
            self.TS.validate({'hello': 'umi'}, 'sub')

        #def test_ins_main(self):
            #print 'run test 3'
            #ins1 = self.ts.build_instance('main')
            #logging.debug('ins::\n' + str(ins1))

        #def test_ins_sub(self):
            #print 'run test 4'
            #ins2 = self.ts.build_instance('sub')
            #logging.debug('ins::\n' + str(ins2))


    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
