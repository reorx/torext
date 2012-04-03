====
Description
====

torext is an instrumental package which aim at easy implementation
of tornado based project.

it help you do the pre works of many essential facilities, like:
    * database connection
    * config file parsing
    * url routing
    * reusable tornado request handler class
    * form handling,
and some common utilities.

it is designed to be used by any tornado project,
but give most priority to nodemix team projects' requirements.


====
Contributing Projects
====

Tornado RPC: https://github.com/joshmarshall/tornadorpc


====
Notes
====
* why not use tornado.options.options ?
  just don't want cause any potential conflict, so tornado's options will not be touched.

* how to debug in testing ?
  logging is mostly used to debug.
  first we should know that there'a a logger called 'test' used in many part of the code already, because 'test' logger is seperated from root logger (propagate = 0), these log recordings would not make difference when the module is inclued.
  nose alone with unittest are used for testing, if log writting happened in test methods directly or from the invoked function or module, they would not be pushed to syserr(IOW, appear on terminal stream) in usual way unless you have manually set a proper handler to them.
  see how logger work, for example a logger called 'a.b', normally it will search for its own handlers and try to handle the record, then go to its parents respectively (-> logger 'b') and do the same thing, finally come to root logger and end.
  back to test methods, nose adds a very special handler to root logger, it will not show you anything normally, but if a test wasn't pass, nose will show you the captured inputs (from print) and logs in the test.
  in order to see logs even tests are pass, there must be a logger that has its own handler (mostly StreamHandler instance), and to avoid root logger's rehandling the record, its must be seperated from that. Additionally, if 'test' logger is involved in your test method, you should add handler and set level to it in TestCase's setUp method.
