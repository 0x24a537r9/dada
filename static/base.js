/* File containing basic functions and global variables. */

var activeBannerIndex = 0;
var bannerMessages = [];
var isShowingBanner = false;

function showBannerMessage(message) {
  bannerMessages.push(message);
  if (!isShowingBanner) {
    rotateBanner();
  }
}

function rotateBanner() {
  var $banners = $('.banner');
  $banners.eq(activeBannerIndex).fadeOut();
  activeBannerIndex = 1 - activeBannerIndex;

  isShowingBanner = bannerMessages.length > 0;
  if (isShowingBanner) {
    var message = bannerMessages[0];
    bannerMessages = bannerMessages.slice(1);

    var $activeBanner = $banners.eq(activeBannerIndex);
    var $activeBannerText = $activeBanner.find('.banner-text');
    $activeBannerText.text(message);
    $activeBanner.fadeIn();
    // Allow a tiny bit of time for the banner to be barely visible.
    setTimeout(function() {
      $activeBannerText.textFit({
        alignVert: true,
        alignHoriz: true,
        multiLine: true,
        reProcess: true,
        maxFontSize: 120
      });
    }, 30);
    setTimeout(rotateBanner, 2500);
  }
}

function getCounter(name) {
  return parseInt(localStorage.getItem('counter-' + name)) || 0;
}

function incCounter(name) {
  var newVal = getCounter(name) + 1;
  localStorage.setItem('counter-' + name, newVal);
  return newVal;
}

function enable($elements) {
  if (!$.isArray($elements)) {
    $elements = [$elements];
  }
  for (var i = 0; i < $elements.length; ++i) {
    $elements[i].prop('disabled', false);
  }
}

function disable($elements) {
  if (!$.isArray($elements)) {
    $elements = [$elements];
  }
  for (var i = 0; i < $elements.length; ++i) {
    $elements[i].prop('disabled', true);
  }
}
