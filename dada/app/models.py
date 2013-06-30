import random
import time

from datetime import datetime
from django.db import models


def ellipsis(width):
  def _decorator(function):
    def _wrapper(*args, **kwargs):
      text = function(*args, **kwargs)
      if len(text) > width:
        return text[:width - 3] + '...'
      else:
        return text
    return _wrapper
  return _decorator


def randint64():
  return random.getrandbits(64) - 2 ** 63


def to_jsonable_timestamp(timestamp):
  return int(time.mktime(timestamp.timetuple()))


class Entry(models.Model):
  id = models.BigIntegerField(blank=True, default=randint64, primary_key=True)
  QUESTION, ANSWER = 'Q', 'A'
  TYPES = {
      QUESTION: 'Question',
      ANSWER: 'Answer',
  }
  type = models.CharField(choices=TYPES.items(), max_length=1)
  text = models.CharField(max_length=64)
  author = models.CharField(max_length=32)
  upvotes = models.PositiveIntegerField(blank=True, default=1)
  downvotes = models.PositiveIntegerField(blank=True, default=0)
  score = models.FloatField(blank=True, default=0.0)
  is_flagged = models.BooleanField(blank=True, default=False)
  created = models.DateTimeField(default=datetime.now, editable=False, blank=True)

  @classmethod
  def get_random(cls, type):
    try:
      return (cls.objects.filter(type=type, is_flagged=False, id__gte=randint64())
                         .order_by('id').all()[0])
    except IndexError:
      # If we shot too high, just get the highest id entry.
      return cls.objects.filter(type=type, is_flagged=False).order_by('-id').all()[0]

  def __unicode__(self):
    return u'%s: %s \u2014 %s on %s' % (Entry.TYPES[self.type], self.text, self.author,
                                        datetime.date(self.created).strftime('%b %d, \'%y'))

  def to_dict(self):
    return {
        'pk': self.pk,
        'text': self.text,
        'author': self.author,
        'upvotes': self.upvotes,
        'downvotes': self.downvotes,
        'score': self.score,
        'created': to_jsonable_timestamp(self.created),
    }

  class Meta:
    get_latest_by = 'created'
    ordering = ['id', '-score', 'created']
