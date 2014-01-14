import base64, os, jinja2, json, struct, webapp2

from functools import wraps
from google.appengine.ext import ndb
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


def to_json(value):
  return json.dumps(value, default=date_time_handler)
JINJA_ENVIRONMENT.filters.update({'to_json': to_json})


def ajax_request(function):
  @wraps(function)
  def wrapper(self, *args, **kwargs):
    output = function(self, *args, **kwargs)
    data = to_json(output)
    self.response.content_type = 'application/json'
    self.response.write(data)
  return wrapper


def encode_ids(ids):
  return base64.urlsafe_b64encode(struct.pack('q' * len(ids), *ids))


def decode_ids(idString):
  return struct.unpack('q' * (len(idString) * 6 / 64), base64.urlsafe_b64decode(idString))


class MainHandler(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('<html><body>Hello world!</body></html>')


class QuestionAnswerHandler(webapp2.RequestHandler):
  @render_to('question_answer.html')
  def get(self, encoded_ids):
    r = Response()
    if encoded_ids:
      ids = decode_ids(encoded_ids)
      r.question = Entry.query(Entry.id == ids[0]).fetch(1)[0].to_dict()
      r.answer = Entry.query(Entry.id == ids[1]).fetch(1)[0].to_dict()
      r.encoded_ids = encoded_ids
    else:
      r.question = Entry.get_random(Entry.QUESTION).to_dict()
      r.answer = Entry.get_random(Entry.ANSWER).to_dict()
      r.encoded_ids = encode_ids((r.question['id'], r.answer['id']))
    return r.__dict__


class AjaxGetQuestionAnswerHandler(webapp2.RequestHandler):
  @ajax_request
  def get(self):
    r = Response()
    r.poems = []
    for i in xrange(0, 10):
      poem = Response()
      poem.question = Entry.get_random(Entry.QUESTION).to_dict()
      poem.answer = Entry.get_random(Entry.ANSWER).to_dict()
      poem.encoded_ids = encode_ids((poem.question['id'], poem.answer['id']))
      r.poems.append(poem.__dict__)
    return r.__dict__


class CreateEntryHandler(webapp2.RequestHandler):
  @render_to('create_entry.html')
  def get(self, entry_type):
    r = Response()
    r.entry_type = entry_type
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


class AjaxVoteHandler(webapp2.RequestHandler):
  @ajax_request
  def post(self):
    r = Response()

    vote = self.request.POST['vote']
    if vote not in ('-1', '0', '1'):
      return Response.errors('Uh, you can\'t vote that many times.')
    vote = int(vote)

    if vote == 0:
      return r.__dict__

    entryKeys = self.request.POST['entryKeys']
    if not entryKeys:
      return Response.errors('What entries are you referring to?')
    entryKeys = [ndb.Key(urlsafe=entryKey) for entryKey in entryKeys.split(',')]

    entries = ndb.get_multi(entryKeys)
    if None in entries:
      return Response.errors('One or more entries is invalid.')

    entryIds = []
    for entry in entries:
      entryIds += [entry.id]
      if vote > 0:
        entry.upvotes += 1
      else:
        entry.downvotes += 1
      entry.put()

    # Note: There is a race-condition here, but it's ok if we lose a few votes here and there.
    poem = Poem.get_or_insert(encode_ids(entryIds))
    if not len(poem.entryKeys):
      poem.entryKeys = entryKeys
      poem.debug_text = ', '.join(entry.text for entry in entries)
    if vote > 0:
      poem.upvotes += 1
    else:
      poem.downvotes += 1
    poem.put()

    return r.__dict__
