import base64, os, jinja2, json, struct, webapp2

from functools import wraps
from google.appengine.ext import ndb
from models import *


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


ENCODED_IDS_KEY = 'encoded_ids'
ENTRY_KEY = 'entry'
ENTRY_KEYS_KEY = 'entry_keys'
ENTRY_TYPE_KEY = 'entry_type'
ERRORS_KEY = 'errors'
POEM_TYPE_KEY = 'poem_type'
POEMS_KEY = 'poems'
SHOW_INSTRUCTIONS_KEY = 'show_instructions'
TEMPLATE_KEY = 'template'

POEM_TYPE_ENTRY_TYPES = {
  Poem.QUESTION_ANSWER: (Entry.QUESTION, Entry.ANSWER),
}


def render_to(template=''):
  def renderer(function):
    @wraps(function)
    def wrapper(self, *args, **kwargs):
      output = function(self, *args, **kwargs)
      if not isinstance(output, dict):
        return output
      tmpl = output.pop(TEMPLATE_KEY, template)
      self.response.write(JINJA_ENVIRONMENT.get_template(tmpl).render(output))
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
  @render_to('home.html')
  def get(self):
    return {}


class PoemHandler(webapp2.RequestHandler):
  @render_to()
  def get(self, poem_type, encoded_ids):
    r = {}
    r[POEM_TYPE_KEY] = poem_type
    r[TEMPLATE_KEY] = '%s.html' % poem_type.replace('-', '_')

    entry_types = POEM_TYPE_ENTRY_TYPES[poem_type]
    entry_keys = []

    if encoded_ids:
      entries = ndb.get_multi(ndb.Key(Entry, id) for id in decode_ids(encoded_ids))
      for i, entry_type in enumerate(entry_types):
        if not entries[i]:
          return {ERRORS_KEY: 'Which entry is that?'}
        elif entry_type != entries[i].type:
          return {ERRORS_KEY: 'Unexpected entry type: %s.' % entries[i].type}
        r[entry_type] = entries[i]
        entry_keys.append(r[entry_type].key.urlsafe())
      r[ENCODED_IDS_KEY] = encoded_ids
      r[SHOW_INSTRUCTIONS_KEY] = False
    else:
      ids = []
      for entry_type in entry_types:
        r[entry_type] = Entry.get_random(entry_type)
        ids.append(r[entry_type].key.id())
        entry_keys.append(r[entry_type].key.urlsafe())
      r[ENCODED_IDS_KEY] = encode_ids(ids)
      r[SHOW_INSTRUCTIONS_KEY] = True

    r[ENTRY_KEYS_KEY] = ','.join(entry_keys)
    return r


class AjaxGetPoemHandler(webapp2.RequestHandler):
  @ajax_request
  def get(self, poem_type):
    r = {POEMS_KEY: []}
    for i in xrange(0, 10):
      poem, ids, keys = {}, [], []
      entries = (Entry.get_random(entry_type) for entry_type in POEM_TYPE_ENTRY_TYPES[poem_type])
      for entry in entries:
        poem[entry.type] = entry
        ids.append(entry.key.id())
        keys.append(entry.key.urlsafe())
      poem[ENCODED_IDS_KEY] = encode_ids(ids)
      poem[ENTRY_KEYS_KEY] = ','.join(keys)
      r[POEMS_KEY].append(poem)

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
    entry = Entry(type=entry_type, text=text, author=author)
    entry.put()
    return {ENTRY_KEY: entry}


class AjaxVoteHandler(webapp2.RequestHandler):
  @ajax_request
  def post(self):
    poem_type = self.request.POST['poem_type']
    if poem_type not in Poem.TYPES:
      return {ERRORS_KEY: 'What kind of poem is that?'}

    vote = self.request.POST['vote']
    if vote not in ('-1', '1'):
      return {ERRORS_KEY: 'Uh, you can\'t vote that many times.'}
    vote = int(vote)

    entry_keys = self.request.POST['entry_keys']
    if not entry_keys:
      return {ERRORS_KEY: 'What entries are you referring to?'}
    entry_keys = [ndb.Key(urlsafe=entry_key) for entry_key in entry_keys.split(',')]

    try:
      self.update_poem(entry_keys, poem_type, vote)
    except Exception as e:
      return {ERRORS_KEY: e.message}

    return {}

  @staticmethod
  @ndb.transactional(xg=True)
  def update_poem(entry_keys, poem_type, vote):
    entries = ndb.get_multi(entry_keys)
    for i, entry_type in enumerate(POEM_TYPE_ENTRY_TYPES[poem_type]):
      if not entry_type:
        raise Exception('One or more entries is invalid.')
      elif entry_type != entries[i].type:
        raise Exception('Unexpected entry type: %s.' % entries[i].type)

    ids = []
    for entry in entries:
      ids += [entry.key.id()]
      if vote > 0:
        entry.upvotes += 1
      else:
        entry.downvotes += 1

    key = ndb.Key(Poem, encode_ids(ids))
    poem = key.get()
    if poem is None:
      poem = Poem(key=key, type=poem_type, entry_keys=entry_keys,
                  debug_text=', '.join(entry.text for entry in entries))
    if vote > 0:
      poem.upvotes += 1
    else:
      poem.downvotes += 1

    ndb.put_multi_async(entries + [poem])

    return poem

