import webapp2

from handlers import *


app = webapp2.WSGIApplication([
    # FE handlers.
    (r'^/$', MainHandler),
    (r'^(?i)/(question-answer)/create/$', CreateEntryHandler),
    (r'^(?i)/(question-answer)/(?:([a-zA-Z0-9_=-]+)/)?$', PoemHandler),
    # AJAX handlers.
    (r'^/x/get-question-answer/$', AjaxGetQuestionAnswerHandler),
    (r'^/x/create-entry/$', AjaxCreateEntryHandler),
    (r'^/x/vote/$', AjaxVoteHandler),
], debug=True)
