import json
from uuid import UUID
from mathutils import Matrix

JSON_FLOAT_PRECISION = 6


def _make_iterencode(markers,
                     _default,
                     _encoder,
                     _indent,
                     _floatstr,
                     _key_separator,
                     _item_separator,
                     _sort_keys,
                     _skipkeys,
                     _one_shot,
                     ):
    '''
    '''

    def _float_str(o):
        '''
        Converts float values using built-in string formatting.
        This will trim trailing zero's and switch to scientific notation
        when it's more compact.
        '''

        o = round(o, JSON_FLOAT_PRECISION)
        o = float("%.*f" % (JSON_FLOAT_PRECISION, o))
        return "%.*g" % (JSON_FLOAT_PRECISION, o)

    def _matrix_list(o):
        '''
        Converts Matrix values to a list of floats
        '''
        list_of_tuples = [r.to_tuple() for r in o]
        flat_list = []
        flat_list_extend = flat_list.extend  # a tiny bit faster
        for t in list_of_tuples:
            flat_list_extend(t)
        return flat_list

    def _iterencode_list(l, level):
        '''

        '''
        if not l:
            yield '[]'
            return
        if markers is not None:
            markerid = id(l)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = l
        buf = '['
        newline_indent = None
        separator = _item_separator
        first = True
        for value in l:
            if first:
                first = False
            else:
                buf = separator
            if isinstance(value, str):
                yield buf + _encoder(value)
            elif value is None:
                yield buf + 'null'
            elif value is True:
                yield buf + 'true'
            elif value is False:
                yield buf + 'false'
            elif isinstance(value, int):
                yield buf + str(value)
            elif isinstance(value, float):
                yield buf + _float_str(value)
            else:
                yield buf
                if isinstance(value, list):
                    chunks = _iterencode_list(value, level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, level)
                else:
                    chunks = _iterencode(value, level)
                for chunk in chunks:
                    yield chunk
        if newline_indent is not None:
            level -= 1
            yield '\n' + _indent * level
        yield ']'
        if markers is not None:
            del markers[markerid]

    def _iterencode_dict(d, level):
        # if not d:
        #     yield '{}'
        #     return
        if markers is not None:
            markerid = id(d)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = d
        yield '{'
        if _indent is not None:
            level += 1
            newline_indent = '\n' + _indent * level
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True
        if _sort_keys:
            items = sorted(d.items(), key=lambda kv: kv[0])
        else:
            items = d.items()
        for key, value in items:
            # if not key:
            #     continue
            if isinstance(value, dict) and not value:
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            elif isinstance(key, str):
                pass
            elif isinstance(key, float):
                key = _float_str(key)
            elif key is True:
                key = 'true'
            elif key is False:
                key = 'false'
            elif key is None:
                key = 'null'
            elif isinstance(key, int):
                key = str(key)
            elif _skipkeys:
                continue
            else:
                raise TypeError("key " + repr(key) + " is not a string")
            if first:
                first = False
            else:
                yield item_separator
            yield _encoder(key)
            yield _key_separator
            if isinstance(value, str):
                yield _encoder(value)
            # elif value is None:
            #     yield 'null'
            elif value is True:
                yield 'true'
            elif value is False:
                yield 'false'
            elif isinstance(value, int):
                yield str(value)
            elif isinstance(value, float):
                yield _float_str(value)
            else:
                if isinstance(value, list):
                    chunks = _iterencode_list(value, level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, level)
                else:
                    chunks = _iterencode(value, level)
                for chunk in chunks:
                    yield chunk
        if newline_indent is not None:
            level -= 1
            yield '\n' + _indent * level
        yield '}'
        if markers is not None:
            del markers[markerid]

    def _iterencode(o, level):
        if isinstance(o, str):
            yield _encoder(o)
        elif o is None:
            yield 'null'
        elif o is True:
            yield 'true'
        elif o is False:
            yield 'false'
        elif isinstance(o, int):
            yield str(o)
        elif isinstance(o, float):
            yield _float_str(o)
        elif isinstance(o, list):
            for chunk in _iterencode_list(o, level):
                yield chunk
        elif isinstance(o, dict):
            for chunk in _iterencode_dict(o, level):
                yield chunk
        elif isinstance(o, UUID):
            yield _encoder(str(o))
        elif isinstance(o, Matrix):
            for chunk in _iterencode_list(_matrix_list(o), level):
                yield chunk
        else:
            if markers is not None:
                markerid = id(o)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            o = _default(o)
            for chunk in _iterencode(o, level):
                yield chunk
            if markers is not None:
                del markers[markerid]

    if _indent is not None and not isinstance(_indent, str):
        _indent = ' ' * _indent

    return _iterencode


# override native json encoder _make_iterencode
json.encoder._make_iterencode = _make_iterencode
