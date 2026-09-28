var fs = require('fs');
var emojiRe = /[\uD83C-\uDBFF][\uDC00-\uDFFF]|[\u2600-\u27BF]|[\uFE00-\uFE0F]/g;
var files = [
  'frontend/index.html',
  'frontend/js/components/analytics.js',
  'frontend/js/components/ideas.js',
  'frontend/js/components/dashboard.js',
  'frontend/standalone.html'
];
var totalEmoji = 0;
files.forEach(function(f) {
  try {
    var content = fs.readFileSync(f, 'utf8');
    var m = content.match(emojiRe) || [];
    if (m.length > 0) { console.log('EMOJI in ' + f + ': ' + m.length); totalEmoji += m.length; }
  } catch(e) { console.log('Skip: ' + f); }
});
console.log('Total emojis: ' + totalEmoji + (totalEmoji === 0 ? ' (PASS)' : ' (FAIL)'));

var html = fs.readFileSync('frontend/index.html', 'utf8');
var ids = ['ideas-analysis-panel','ideas-results','previous-ideas','dashboard-market-gaps','analytics-market-gaps','module-gaps'];
ids.forEach(function(id) {
  var found = html.indexOf('id="' + id + '"') !== -1;
  console.log('#' + id + ': ' + (found ? 'OK' : 'MISSING'));
});

// Check JS files syntax
var jsFiles = [
  'frontend/js/components/analytics.js',
  'frontend/js/components/ideas.js',
  'frontend/js/components/dashboard.js'
];
jsFiles.forEach(function(f) {
  try {
    var code = fs.readFileSync(f, 'utf8').replace(/^export\s+/m, '');
    new Function(code);
    console.log(f + ': SYNTAX OK');
  } catch(e) {
    console.log(f + ' SYNTAX ERROR: ' + e.message);
  }
});
