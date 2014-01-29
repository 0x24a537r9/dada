import webapp2

from handlers import *
from models import *


app = webapp2.WSGIApplication([
    # FE handlers.
    (r'^/$', MainHandler),
    (r'^(?i)/(%s)/create/$' % '|'.join(Poem.TYPES), CreatePoemHandler),
    (r'^(?i)/(%s)/(?:([a-zA-Z0-9_=-]+)/)?$' % '|'.join(Poem.TYPES), PoemHandler),
    # AJAX handlers.
    (r'^/x/get-(%s)/$' % '|'.join(Poem.TYPES), AjaxGetPoemHandler),
    (r'^/x/create-entries/$', AjaxCreateEntriesHandler),
    (r'^/x/vote/$', AjaxVoteHandler),
], debug=True)
