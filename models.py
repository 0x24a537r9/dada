import datetime, math, random

from google.appengine.ext import ndb


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


class Model(ndb.Model):
  def to_dict(self):
    ret = ndb.Model.to_dict(self)
    ret['key'] = self.key.urlsafe()
    return ret


class Entry(Model):
  order = ndb.ComputedProperty(lambda self: randint64(), indexed=True)

  TYPES = QUESTION, ANSWER = 'question', 'answer'
  type = ndb.StringProperty(required=True, choices=TYPES, indexed=True)
  
  text = ndb.StringProperty(required=True, indexed=False)
  author = ndb.StringProperty(required=True, default='Anonymous', indexed=False)
  
  upvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  downvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  score = ndb.ComputedProperty(lambda self: compute_score(self.upvotes, self.downvotes),
                               indexed=True)
  
  is_flagged = ndb.BooleanProperty(required=True, default=False, indexed=True)
  created = ndb.DateTimeProperty(required=True, auto_now_add=datetime.datetime.now)

  @classmethod
  def get_random(cls, type):
    result = (cls.query(cls.type == type, cls.order >= randint64(), cls.is_flagged == False)
                 .order(cls.order)
                 .fetch(1))
    # If we shot too high, just get the lowest order entry.
    if len(result) == 0:
      result = cls.query(cls.type == type, cls.is_flagged == False).order(cls.order).fetch(1)
    return result[0]

  def __unicode__(self):
    return u'%s: %s \u2014 %s on %s' % (self.type, self.text, self.author,
                                        datetime.date(self.created).strftime('%b %d, \'%y'))


class Poem(Model):
  order = ndb.ComputedProperty(lambda self: randint64(), indexed=True)

  TYPES = QUESTION_ANSWER, CONDITIONALS, THE_EXQUISITE_CORPSE = ('question-answer', 'conditionals',
                                                                 'the-exquisite-corpse')
  type = ndb.StringProperty(required=True, choices=TYPES, indexed=True)

  entry_keys = ndb.KeyProperty(kind=Entry, repeated=True, indexed=False)

  upvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  downvotes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  score = ndb.ComputedProperty(lambda self: compute_score(self.upvotes, self.downvotes),
                               indexed=True)

  debug_text = ndb.StringProperty(indexed=False)
