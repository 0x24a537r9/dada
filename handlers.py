import os
import jinja2
import json
import webapp2

from functools import wraps
from models import *


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


# Attributes will be defined outside init pylint: disable=W0201
class Response(object):
  @classmethod
  def errors(cls, *errors):
    if len(errors) == 1 and hasattr(errors[0], '__iter__'):
      return {'errors': errors[0]}
    else:
      return {'errors': errors}


def render_to(template=''):
  def renderer(function):
    @wraps(function)
    def wrapper(self, *args, **kwargs):
      output = function(self, *args, **kwargs)
      self.response.write(JINJA_ENVIRONMENT.get_template(template).render(output))
    return wrapper
  return renderer


def date_time_handler(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        raise TypeError("%r is not JSON serializable" % obj)


def ajax_request(function):
    @wraps(function)
    def wrapper(self, *args, **kwargs):
      output = function(self, *args, **kwargs)
      data = json.dumps(output, default=date_time_handler)
      self.response.content_type = 'application/json'
      self.response.write(data)
    return wrapper


class MainHandler(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('<html><body>Hello world!</body></html>')


class QuestionAnswerHandler(webapp2.RequestHandler):
  @render_to('question_answer.html')
  def get(self):
    return {
      'testvalue': 'sldjfsdljf',
    }


class CreateEntryHandler(webapp2.RequestHandler):
  @render_to('create_entry.html')
  def get(self, entry_type):
    return {
      'entry_type': entry_type,
    }


class AjaxGetQuestionAnswerHandler(webapp2.RequestHandler):
  @ajax_request
  def get(self):
    r = Response()
    r.question = Entry.get_random(Entry.QUESTION).to_dict()
    r.answer = Entry.get_random(Entry.ANSWER).to_dict()
    return r.__dict__


class AjaxCreateEntryHandler(webapp2.RequestHandler):
  @ajax_request
  def post(self):
    r = Response()

    entry_type = self.request.POST['entry_type']
    if entry_type not in Entry.TYPES:
      return Response.errors('What kind of entry is that?')

    text = self.request.POST['text'].strip()
    if len(text) == 0:
      return Response.errors('You forgot your entry!')
    elif len(text) > 64:
      return Response.errors('Your entry is too long!')

    author = self.request.POST['author'].strip()
    if len(author) == 0:
      return Response.errors('You forgot your name!')
    elif len(author) > 32:
      return Response.errors('Your name is too long!')

    # TODO: Entry-type-specific length-check.
    entry = Entry(id=randint64(), type=entry_type, text=text, author=author)
    entry.put()
    r.entry = entry.to_dict()

    return r.__dict__
