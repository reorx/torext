#!/usr/bin/python
# -*- coding: utf-8 -*-


def start_shell(local_vars={}):
    import os
    import code
    import readline
    import rlcompleter

    class irlcompleter(rlcompleter.Completer):
        def complete(self, text, state):
            if text == "":
                #you could  replace \t to 4 or 8 spaces if you prefer indent via spaces
                return ['    ', None][state]
            else:
                return rlcompleter.Completer.complete(self, text, state)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(irlcompleter().complete)

    pythonrc = os.environ.get("PYTHONSTARTUP")
    if pythonrc and os.path.isfile(pythonrc):
        try:
            execfile(pythonrc)
        except NameError:
            pass
    # This will import .pythonrc.py as a side-effect
    import user

    _locals = locals()
    for i in _locals:
        if not i.startswith('__') and i != 'local_vars':
            local_vars[i] = _locals[i]
    local_vars.update({
        '__name__': '__main__',
        '__package__': None,
        '__doc__': None,
    })

    # TODO problem: could not complete exising vars.

    code.interact(local=local_vars)


if __name__ == '__main__':
    print 'test start_shell()'
    start_shell()
