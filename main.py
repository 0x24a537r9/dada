import webapp2

from handlers import *


app = webapp2.WSGIApplication([
    # FE handlers.
    (r'^/$', MainHandler),
    (r'^(?i)/question-answer/?$', QuestionAnswerHandler),
    (r'^(?i)/(question-answer)/create/?$', CreateEntryHandler),
    # AJAX handlers.
    (r'^/x/get-question-answer/$', AjaxGetQuestionAnswerHandler),
    (r'^/x/create-entry/$', AjaxCreateEntryHandler),
], debug=True)
