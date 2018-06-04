/* AJAX functions + functions to help with CSRF tokens.
 *
 * CSRF functions adapted from https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax.
 */

var csrftoken = $.cookie('csrftoken');

function isCsrfSafeMethod(method) {
  // These HTTP methods do not require CSRF protection.
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
  // Test that a given url is a same-origin URL.
  // The url could be relative or scheme relative or absolute.
  var host = document.location.host;  // Includes port.
  var protocol = document.location.protocol;
  var sr_origin = '//' + host;
  var origin = protocol + sr_origin;
  // Allow absolute or scheme relative URLs to same origin.
  return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
      (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
      // ... or any other URL that isn't scheme relative or absolute i.e relative.
      !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!isCsrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

function createEntries(entryTypes, $entries, $author) {
  var hasEntryText = false;
  $entries.each(function(i, entry) {
    if ($(entry).val().trim()) {
      hasEntryText = true;
      return false;
    }
  });
  if (!hasEntryText) {
    return;
  }

  disable([$entries, $author]);

  var data = {};
  data.entry_types = entryTypes;
  data.entry_texts = [];
  $entries.each(function(i, entry) {
    data.entry_texts.push($(entry).val().trim());
  });
  data.author = $author.val();
  $.post('/x/create-entries/', data, function (data) {
    if (data.errors) {
      showBannerMessage(data.errors);
      return;
    }
    $entries.val('');
    localStorage.setItem('author', $author.val());
    showBannerMessage('Thanks for contributing!');
    if (!localStorage.getItem('hasCreated')) {
      localStorage.setItem('hasCreated', true);
      showBannerMessage('How about another?');
    }
  }).fail(function() {
    showBannerMessage('Uh-oh, we done goofed!');
  }).always(function() {
    enable([$entries, $author]);
  });
}

function sendVote(poemType, encodedIds, vote) {
  if (vote != 1 && vote != -1) {
    return;
  }

  var data = {};
  data.poem_type = poemType
  data.encoded_ids = encodedIds;
  data.vote = vote;
  $.post('/x/vote/', data, function (data) {
    if (data.errors) {
      console.error(data.errors);
    }
  }).fail(function() { console.error('Server error!'); });
}
