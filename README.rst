====
Description
====

Torext is an utilities bundle for tornado, aimed at easy development & deployment of tornado application.

Tornado is a great library, but sometimes I found it not that convenitent to use, for example,
I have to manually import handlers for Application initialization when there are more than one modules
that hold request handlers, I have to write `define('myoption')` for a lot of line, they are unsightly and inconvenient to manipulate.
Each time I encounter those problems, my developing process is desturbed, I have to either consult the code
I wrote in old project, or type many repetitive code. Tornado is elegant, so I think developing with tornado
should also be elegant.

That's what torext is created for, it contains features that most web framework commonly have,
some are redefines some are additional:

* database integration and models

* url routing

* validator for everything and request

* error handling dispatch

* project scaffold

* invoke settings from file

* unit testing
