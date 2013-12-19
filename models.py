import datetime
import random

from google.appengine.ext import ndb



def randint64():
  return random.getrandbits(64) - 2 ** 63


class Model(ndb.Model):
  def to_dict(self):
    ret = ndb.Model.to_dict(self)
    ret['key'] = self.key.urlsafe()
    return ret


class Entry(Model):
  id = ndb.IntegerProperty(required=True, indexed=True)

  TYPES = QUESTION, ANSWER = 'Question', 'Answer'
  type = ndb.StringProperty(required=True, choices=TYPES, indexed=True)
  
  text = ndb.StringProperty(required=True)
  author = ndb.StringProperty(required=True, default='Anonymous')
  
  upvotes = ndb.IntegerProperty(required=True, default=1)
  downvotes = ndb.IntegerProperty(required=True, default=0)
  score = ndb.FloatProperty(required=True, default=0.0, indexed=True)
  
  is_flagged = ndb.BooleanProperty(required=True, default=False, indexed=True)
  created = ndb.DateTimeProperty(required=True, auto_now_add=datetime.datetime.now)

  @classmethod
  def get_random(cls, type):
    result = (cls.query(cls.type == type, cls.id >= randint64(), cls.is_flagged == False)
                 .order(cls.id)
                 .fetch(1))
    # If we shot too high, just get the lowest id entry.
    if len(result) == 0:
      result = cls.query(cls.type == type, cls.is_flagged == False).order(-cls.id).fetch(1)
    return result[0]

  def __unicode__(self):
    return u'%s: %s \u2014 %s on %s' % (self.type, self.text, self.author,
                                        datetime.date(self.created).strftime('%b %d, \'%y'))
