/* File containing basic functions and global variables. */

function getCounter(name) {
  return parseInt(localStorage.getItem('counter-' + name)) || 0;
}

function incCounter(name) {
  var newVal = getCounter(name) + 1;
  localStorage.setItem('counter-' + name, newVal);
  return newVal;
}

function randEntry() {
  var entryTypes = ['Q', 'A'];
  return entryTypes[Math.floor(Math.random() * entryTypes.length)]
}