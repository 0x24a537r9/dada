import base64, os, jinja2, json, struct, webapp2

from functools import wraps
from google.appengine.ext import ndb
from models import *


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


ERRORS_KEY = 'errors'
POEM_TYPE_KEY = 'poem_type'
POEMS_KEY = 'poems'
ENCODED_IDS_KEY = 'encoded_ids'
ENTRY_KEYS_KEY = 'entry_keys'
ENTRY_TYPE_KEY = 'entry_type'
ENTRY_KEY = 'entry'


def render_to(template=''):
  def renderer(function):
    @wraps(function)
    def wrapper(self, *args, **kwargs):
      output = function(self, *args, **kwargs)
      self.response.write(JINJA_ENVIRONMENT.get_template(template).render(output))
    return wrapper
  return renderer


def json_handler(obj):
  if isinstance(obj, datetime.datetime):
    return obj.isoformat()
  elif isinstance(obj, Model):
    return obj.to_dict()
  else:
    raise TypeError("%r is not JSON serializable" % obj)


def to_json(value):
  return json.dumps(value, default=json_handler)
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


class PoemHandler(webapp2.RequestHandler):
  @render_to('question_answer.html')
  def get(self, poem_type, encoded_ids):
    r = {}
    r[POEM_TYPE_KEY] = poem_type
    if poem_type == 'question-answer':
      entry_types = (Entry.QUESTION, Entry.ANSWER)
    entry_keys = []

    if encoded_ids:
      ids = decode_ids(encoded_ids)
      for i, entry_type in enumerate(entry_types):
        r[entry_type] = Entry.query(Entry.id == ids[i]).fetch(1)[0]
        entry_keys.append(r[entry_type].key.urlsafe())
      r[ENCODED_IDS_KEY] = encoded_ids
    else:
      ids = []
      for entry_type in entry_types:
        r[entry_type] = Entry.get_random(entry_type)
        ids.append(r[entry_type].id)
        entry_keys.append(r[entry_type].key.urlsafe())
      r[ENCODED_IDS_KEY] = encode_ids(ids)

    r[ENTRY_KEYS_KEY] = ','.join(entry_keys)
    return r


class AjaxGetQuestionAnswerHandler(webapp2.RequestHandler):
  @ajax_request
  def get(self):
    r = {POEMS_KEY: []}
    for i in xrange(0, 10):
      question, answer = Entry.get_random(Entry.QUESTION), Entry.get_random(Entry.ANSWER)
      r[POEMS_KEY].append({
          Entry.QUESTION: question,
          Entry.ANSWER: answer,
          ENCODED_IDS_KEY: encode_ids((question.id, answer.id)),
          ENTRY_KEYS_KEY: ','.join((question.key.urlsafe(), answer.key.urlsafe())),
      })
    return r


class CreateEntryHandler(webapp2.RequestHandler):
  @render_to('create_entry.html')
  def get(self, entry_type):
    return {ENTRY_TYPE_KEY: entry_type}


class AjaxCreateEntryHandler(webapp2.RequestHandler):
  @ajax_request
  def post(self):
    entry_type = self.request.POST['entry_type']
    if entry_type not in Entry.TYPES:
      return {ERRORS_KEY: 'What kind of entry is that?'}

    text = self.request.POST['text'].strip()
    if len(text) == 0:
      return {ERRORS_KEY: 'You forgot your entry!'}
    elif len(text) > 64:
      return {ERRORS_KEY: 'Your entry is too long!'}

    author = self.request.POST['author'].strip()
    if len(author) == 0:
      return {ERRORS_KEY: 'You forgot your name!'}
    elif len(author) > 32:
      return {ERRORS_KEY: 'Your name is too long!'}

    # TODO: Entry-type-specific length-check.
    entry = Entry(id=randint64(), type=entry_type, text=text, author=author)
    entry.put()
    return {ENTRY_KEY: entry}


class AjaxVoteHandler(webapp2.RequestHandler):
  @ajax_request
  def post(self):
    vote = self.request.POST['vote']
    if vote not in ('-1', '1'):
      return {ERRORS_KEY: 'Uh, you can\'t vote that many times.'}
    vote = int(vote)

    entry_keys = self.request.POST['entry_keys']
    if not entry_keys:
      return {ERRORS_KEY: 'What entries are you referring to?'}
    entry_keys = [ndb.Key(urlsafe=entry_key) for entry_key in entry_keys.split(',')]

    entries = ndb.get_multi(entry_keys)
    if None in entries:
      return {ERRORS_KEY: 'One or more entries is invalid.'}

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
    if not len(poem.entry_keys):
      poem.entry_keys = entry_keys
      poem.debug_text = ', '.join(entry.text for entry in entries)
    if vote > 0:
      poem.upvotes += 1
    else:
      poem.downvotes += 1
    poem.put()

    return {}
