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

function loadQuestionAnswer(questionEl, answerEl, loadEl, errorEl, createEl) {
  loadEl.attr('disabled', true);

  var data = {};
  $.ajax({
    url: '/x/get-question-answer/',
    data: data,
    cache: false,
    success: function (data) {
      if (data.errors) {
        errorEl.text(data.errors.join());
        return;
      }
      questionEl.text(data.question.text);
      answerEl.text(data.answer.text);
      if (incCounter('question-answer-poems-viewed') >= 5) {
        createEl.show();
      }
    }
  }).fail(function() {
    errorEl.text('Uh-oh, we done goofed!');
  }).always(function() {
    loadEl.removeAttr('disabled');
  });
}

function createEntry(entryType, textEl, authorEl, errorEl, success) {
  textEl.attr('disabled', true);
  authorEl.attr('disabled', true);

  var data = {};
  data.entry_type = entryType;
  data.text = textEl.val();
  data.author = authorEl.val();
  $.post('/x/create-entry/', data, function (data) {
    if (data.errors) {
      errorEl.text(data.errors.join());
      return;
    }
    textEl.val('');
    localStorage.setItem('author', authorEl.val());
    success();
  }).fail(function() {
    errorEl.text('Uh-oh, we done goofed!');
  }).always(function() {
    textEl.removeAttr('disabled');
    authorEl.removeAttr('disabled');
  });
}
