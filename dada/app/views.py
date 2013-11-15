from annoying.decorators import ajax_request, render_to
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404
from django.shortcuts import *
from models import *
from validators import *


# Attributes will be defined outside init pylint: disable=W0201
class Response(object):
  @classmethod
  def errors(cls, *errors):
    if len(errors) == 1 and hasattr(errors[0], '__iter__'):
      return {'errors': errors[0]}
    else:
      return {'errors': errors}


@render_to('home.html')
def home(request):
  r = Response()
  return r.__dict__


@render_to('question_answer.html')
def question_answer(request):
  r = Response()
  return r.__dict__


@render_to('create_entry.html')
def create_entry(request, entry_type):
  r = Response()
  return r.__dict__


@ajax_request
def ajax_get_question_answer(request):
  r = Response()
  if request.method != 'GET':
    return Response.errors('Request must use GET; used: %s.' % request.method)

  r.question = Entry.get_random(Entry.QUESTION).to_dict()
  r.answer = Entry.get_random(Entry.ANSWER).to_dict()

  return r.__dict__


@ajax_request
def ajax_create_entry(request):
  r = Response()
  if request.method != 'POST':
    return Response.errors('Request must use POST; used: %s.' % request.method)

  entry_type = request.POST['entry_type']
  if entry_type not in Entry.TYPES:
    return Response.errors('What kind of entry is that?')

  text = request.POST['text'].strip()
  if len(text) == 0:
    return Response.errors('You forgot your entry!')
  elif len(text) > 64:
    return Response.errors('Your entry is too long!')

  author = request.POST['author'].strip()
  if len(author) == 0:
    return Response.errors('You forgot your name!')
  elif len(author) > 32:
    return Response.errors('Your name is too long!')

  # TODO: Entry-type-specific length-check.
  entry = Entry(type=entry_type, text=text, author=author)
  entry.save()
  r.entry = entry.to_dict()

  return r.__dict__
