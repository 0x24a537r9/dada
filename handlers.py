import os, jinja2, json, logging, traceback, webapp2

from functools import wraps
from google.appengine.api import memcache
from google.appengine.ext import ndb
from models import *
from urllib import urlencode


POEMS_TO_FETCH = 10
NEW_POEMS_TO_FETCH = int(round(0.7 * POEMS_TO_FETCH))


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
JINJA_ENVIRONMENT.filters.update({'urlencode': lambda s: urlencode({'': s.encode('utf8')})[1:]})


def rate_limit(seconds_per_request=1):
  def rate_limiter(function):
    @wraps(function)
    def wrapper(self, *args, **kwargs):
      added = memcache.add('%s:%s' % (self.__class__.__name__, self.request.remote_addr or ''), 1,
                           time=seconds_per_request, namespace='rate_limiting')
      if not added:
        self.response.write('Rate limit exceeded.')
        self.response.set_status(403)
        return
      return function(self, *args, **kwargs)
    return wrapper
  return rate_limiter


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
  elif isinstance(obj, ndb.Model):
    return obj.to_dict()
  else:
    raise TypeError("%r is not JSON serializable" % obj)


def to_json(value):
  return json.dumps(value, default=json_handler)
JINJA_ENVIRONMENT.filters.update({'to_json': lambda obj: jinja2.Markup(to_json(obj))})


def ajax_request(function):
  @wraps(function)
  def wrapper(self, *args, **kwargs):
    try:
      output = function(self, *args, **kwargs)
    except Exception as e:
      logging.error(traceback.format_exc())
      output = {ERRORS_KEY: 'Unexpected exception! %s: %s' % (e.__class__.__name__, e)}
    data = to_json(output)
    self.response.content_type = 'application/json'
    self.response.write(data)
  return wrapper


def get_poems(poem_type, encoded_ids=None, rank=None):
  poems = []

  if encoded_ids:
    poem = ndb.Key(Poem, encoded_ids).get()
    if poem == None:
      try:
        ids = decode_ids(encoded_ids)
        poem = Poem(type=poem_type, entry_keys=[ndb.Key(Entry, id) for id in ids])
        # Ensure the entries are valid here before adding them to the list.
        poem.fetch_entries()
      except Exception as e:
        logging.error('Could not fetch poem "%s": %s', encoded_ids, e.message)
        poem = None

    if poem != None:
      poems.append(poem)

  if not poems and rank != None:
    poems += Poem.get_ranked(poem_type, rank, POEMS_TO_FETCH)

  if len(poems) < POEMS_TO_FETCH:
    for i in xrange(NEW_POEMS_TO_FETCH):
      poems.append(Poem.create_random(poem_type))

    poems += Poem.get_random(poem_type, POEMS_TO_FETCH - NEW_POEMS_TO_FETCH)

  for poem in poems:
    poem.fetch_entries()
  return poems


class WarmupHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=10)
  def get(self):
    self.response.write('Warmed up!')


class HomeHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=10)
  @render_to('home.html')
  def get(self):
    return {}


class PoemHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=1)
  @render_to()
  def get(self, poem_type, encoded_ids):
    r = {}
    r[POEM_TYPE_KEY] = poem_type
    r[TEMPLATE_KEY] = '%s.html' % poem_type.replace('-', '_')

    r[ENCODED_IDS_KEY] = encoded_ids
    r[SHOW_INSTRUCTIONS_KEY] = True
    if encoded_ids:
      if encoded_ids == 'top':
        r[POEMS_KEY] = get_poems(poem_type, rank=0)
        r[SHOW_INSTRUCTIONS_KEY] = False
      else:
        r[POEMS_KEY] = get_poems(poem_type, encoded_ids=encoded_ids)
    else:
      r[POEMS_KEY] = get_poems(poem_type)

    return r


class PoemPreviewHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=1)
  @render_to()
  def get(self, poem_type, encoded_ids):
    r = {}
    r[POEM_TYPE_KEY] = poem_type
    r[TEMPLATE_KEY] = '%s_preview.html' % poem_type.replace('-', '_')

    r[ENCODED_IDS_KEY] = encoded_ids
    r[POEMS_KEY] = get_poems(poem_type, encoded_ids=encoded_ids)

    return r


class AjaxGetPoemHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=5)
  @ajax_request
  def get(self, poem_type):
    rank = self.request.GET.get('rank')
    if rank != None:
      try:
        rank = int(rank)
      except:
        return {ERRORS_KEY: 'That\'s not a valid rank.'}

    return {POEMS_KEY: get_poems(poem_type, rank=rank)}


class CreatePoemHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=1)
  @render_to()
  def get(self, poem_type):
    r = {}
    r[POEM_TYPE_KEY] = poem_type
    r[ENTRY_TYPES_KEY] = POEM_TYPE_ENTRY_TYPES[poem_type]
    r[TEMPLATE_KEY] = 'create_%s.html' % poem_type.replace('-', '_')

    return r


class AjaxCreateEntriesHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=2)
  @ajax_request
  def post(self):
    entry_types = self.request.POST.getall('entry_types[]')
    for entry_type in entry_types:
      if entry_type not in Entry.TYPES:
        return {ERRORS_KEY: 'What kind of entry is that?'}

    author = self.request.POST['author'].strip()
    if len(author) == 0:
      return {ERRORS_KEY: 'You forgot your name!'}
    elif len(author) > 32:
      return {ERRORS_KEY: 'Your name is too long!'}

    entries = []
    entry_texts = [entry.strip() for entry in self.request.POST.getall('entry_texts[]')]
    if len(entry_types) != len(entry_texts):
      return {ERRORS_KEY: 'The number of entry texts doesn\'t match the number of entry types...'}

    for entry_type, entry_text in zip(entry_types, entry_texts):
      # TODO: Entry-type-specific length-check.
      if len(entry_text) == 0:
        continue
      elif len(entry_text) > 64:
        return {ERRORS_KEY: 'Your entry is too long!'}
      entries.append(Entry(type=entry_type, text=entry_text, author=author))

    ndb.put_multi(entries)
    return {}


class AjaxVoteHandler(webapp2.RequestHandler):
  @rate_limit(seconds_per_request=1)
  @ajax_request
  def post(self):
    poem_type = self.request.POST['poem_type']
    if poem_type not in Poem.TYPES:
      return {ERRORS_KEY: 'What kind of poem is that?'}

    vote = self.request.POST['vote']
    if vote not in ('-1', '1'):
      return {ERRORS_KEY: 'Uh, you can\'t vote that many times.'}
    vote = int(vote)

    encoded_ids = self.request.POST['encoded_ids']
    if not encoded_ids:
      return {ERRORS_KEY: 'What entries are you referring to?'}
    try:
      entry_keys = [ndb.Key(Entry, id) for id in decode_ids(encoded_ids)]
    except Exception as e:
      return {ERRORS_KEY: 'Could not decode ids "%s": %s.' % (encoded_ids, e)}

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
