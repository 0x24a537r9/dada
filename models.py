import base64, datetime, math, random, struct

from google.appengine.ext import ndb


AUTHOR_KEY = 'author'
ENCODED_IDS_KEY = 'encoded_ids'
ENTRY_KEY = 'entry'
ENTRY_TYPE_KEY = 'entry_type'
ENTRY_TYPES_KEY = 'entry_types'
ERRORS_KEY = 'errors'
POEM_TYPE_KEY = 'poem_type'
POEMS_KEY = 'poems'
RANK_KEY = 'rank'
SHOW_INSTRUCTIONS_KEY = 'show_instructions'
TEMPLATE_KEY = 'template'
TEXT_KEY = 'text'
TYPE_KEY = 'type'


def randint64():
  return random.getrandbits(64) - 2 ** 63


def compute_score(upvotes, downvotes):
  z = 1.96
  n = float(upvotes + downvotes)
  if n == 0:
    return 0
  phat = upvotes / float(n)
  return ((phat + z * z / (2 * n) - z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)) /
          (1 + z * z / n))


def encode_ids(ids):
  return base64.urlsafe_b64encode(struct.pack('q' * len(ids), *ids))


def decode_ids(idString):
  idAsciiString = idString.encode('ascii')
  return struct.unpack('q' * (len(idAsciiString) * 6 / 64), base64.urlsafe_b64decode(idAsciiString))


class Entry(ndb.Model):
  order = ndb.ComputedProperty(lambda self: randint64(), indexed=True)

  TYPES = QUESTION, ANSWER, CONDITION, CONSEQUENCE = (
      'question', 'answer', 'condition', 'consequence'
  )
  type = ndb.StringProperty(required=True, choices=TYPES, indexed=True)
  
  text = ndb.StringProperty(required=True, indexed=False)
  author = ndb.StringProperty(required=True, default='Anonymous', indexed=False)
  
  upvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  downvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  score = ndb.ComputedProperty(lambda self: compute_score(self.upvotes, self.downvotes),
                               indexed=True)
  
  is_flagged = ndb.BooleanProperty(required=True, default=False, indexed=True)
  created = ndb.DateTimeProperty(required=True, indexed=False, auto_now_add=datetime.datetime.now)

  @classmethod
  def get_random(cls, type):
    result = (cls.query(cls.type == type, cls.order >= randint64(), cls.is_flagged == False)
                 .order(cls.order)
                 .fetch(1))
    # If we shot too high, just get the lowest order entry.
    if len(result) == 0:
      result = cls.query(cls.type == type, cls.is_flagged == False).order(cls.order).fetch(1)
    return result[0]

  def to_dict(self):
    return {
        TEXT_KEY: self.text,
        AUTHOR_KEY: self.author,
    }


class Poem(ndb.Model):
  order = ndb.ComputedProperty(lambda self: randint64(), indexed=True)

  TYPES = QUESTION_ANSWER, CONDITIONAL, THE_EXQUISITE_CORPSE = ('question-answer', 'conditional',
                                                                 'the-exquisite-corpse')
  type = ndb.StringProperty(required=True, choices=TYPES, indexed=True)

  entry_keys = ndb.KeyProperty(kind=Entry, repeated=True, indexed=False)
  entries = []

  upvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  downvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  score = ndb.ComputedProperty(lambda self: compute_score(self.upvotes, self.downvotes),
                               indexed=True)

  debug_text = ndb.StringProperty(indexed=False)

  rank = None

  @classmethod
  def create_random(cls, type):
    poem = cls(type=type)
    poem.entries = [Entry.get_random(entry_type) for entry_type in POEM_TYPE_ENTRY_TYPES[type]]
    poem.entry_keys = [entry.key for entry in poem.entries]
    poem.debug_text = ', '.join(entry.text for entry in poem.entries)
    return poem

  @classmethod
  def get_random(cls, type, n):
    return cls.query(cls.type == type, cls.order >= randint64()).order(cls.order).fetch(n)

  @classmethod
  def get_ranked(cls, type, rank, n):
    poems = cls.query(cls.type == type).order(-cls.score).fetch(n, offset=rank)
    for i, poem in enumerate(poems, start=rank):
      poem.rank = i
    return poems

  def fetch_entries(self):
    self.entries = self.entries or ndb.get_multi(self.entry_keys)
    if None in self.entries:
      raise Exception('Invalid entry key.')

  def to_dict(self):
    d = {TYPE_KEY: self.type}
    self.fetch_entries()
    for i, entry_type in enumerate(POEM_TYPE_ENTRY_TYPES[self.type]):
      d[entry_type] = self.entries[i]
    d[ENCODED_IDS_KEY] = encode_ids(tuple(entry.key.id() for entry in self.entries))
    d[RANK_KEY] = self.rank
    return d


POEM_TYPE_ENTRY_TYPES = {
  Poem.QUESTION_ANSWER: (Entry.QUESTION, Entry.ANSWER),
  Poem.CONDITIONAL: (Entry.CONDITION, Entry.CONSEQUENCE),
}
