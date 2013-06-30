# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Entry'
        db.create_table(u'app_entry', (
            ('id', self.gf('django.db.models.fields.BigIntegerField')(default=3008218264966498284L, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('upvotes', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, blank=True)),
            ('downvotes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('score', self.gf('django.db.models.fields.FloatField')(default=0.0, blank=True)),
            ('is_flagged', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
        ))
        db.send_create_signal(u'app', ['Entry'])


    def backwards(self, orm):
        # Deleting model 'Entry'
        db.delete_table(u'app_entry')


    models = {
        u'app.entry': {
            'Meta': {'ordering': "['id', '-score', 'created']", 'object_name': 'Entry'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'downvotes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'default': '15413891766764611434L', 'primary_key': 'True'}),
            'is_flagged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'score': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'upvotes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'})
        }
    }

    complete_apps = ['app']