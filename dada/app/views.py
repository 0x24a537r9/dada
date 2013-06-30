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


@ajax_request
def ajax_get_question_answer(request):
  r = Response()
  if request.method != 'GET':
    return Response.errors('Request must use GET; used: %s.' % request.method)

  r.question = Entry.get_random(Entry.QUESTION).to_dict()
  r.answer = Entry.get_random(Entry.ANSWER).to_dict()

  return r.__dict__
