function main () {
  pitch();
  setHR()
  setRefDictLink()
  setMemoClassOfJpNotes()
}

function pitch () {
const divKana = document.querySelector(".kana");
const divAccent = document.querySelector(".accent");
const kanaStr = divKana.textContent;
const accentStr = divAccent.textContent;
divAccent.style.display = "none";
if (!accentStr) 
  return;

const kanaList = kanaStr.split(";");
const accentList = accentStr.split(";");
if (kanaList.length !== accentList.length)
  return;

divKana.innerHTML = "";
for (let i = 0; i < kanaList.length; i++) {
  const kana = kanaList[i];
  const accent = accentList[i];
  const div = document.createElement("span");
  div.className = "kana_entry";
  const pitches = accent.split(",");
  pitches.forEach(pitch => {
    const moras = kana.split(/(?![ゃゅょぁぃぅぇぉャュョァィゥェォ])/)
    const span = document.createElement("span");
    span.className = "pitch";
    let pitch_list = []
    let moras_list = []
    if (pitch.indexOf('_') != -1) { // format: 2@3_0@4  (前の３拍のアクセントは2で、後の4拍のアクセントは0)
      let start_idx = 0
      pitch.split('_').forEach(part => {
        const pitch_moras = part.split('@')
        const part_pitch = pitch_moras[0]
        const moras_num = pitch_moras[1]
        const end_idx = start_idx + parseInt(moras_num)
        pitch_list.push(part_pitch)
        moras_list.push(moras.slice(start_idx, end_idx))
        start_idx = end_idx
      }) 
    } else {
      pitch_list = [pitch]
      moras_list = [moras]
    }
    for (let i = 0; i < moras_list.length; i++) {
      const moras_ = moras_list[i]
      const pitch_ = pitch_list[i]
      const span_ = document.createElement("span");
      if (pitch_ > 0) {
        moras_[pitch_ - 1] = `<span class="descent">${moras_[pitch_ - 1]}</span>`;
      }
      var l = pitch_ > 0 ? pitch_ - 2 : moras_.length - 1;
      if (l > 0) {
        moras_[l] += "</span>";
        moras_[1] = "<span class=\"flat\">" + moras_[1];
      }
      span_.innerHTML += moras_.join('');
      span.appendChild(span_)
    }
    div.append(span);
  })
  divKana.append(div);
}
const BORDER = "solid 1px";
document.querySelectorAll(".pitch .flat").forEach(pi => {
  pi.style["border-top"] = BORDER;
})
document.querySelectorAll(".pitch .descent").forEach(pi => {
  const color = window.getComputedStyle(pi).color;
  const tinyImage = createTinyImage(color);
  pi.style["border-top"] = BORDER;
  pi.style["background-image"] = `url("${tinyImage}")`;
  pi.style["background-size"] = "1px 0.36em";
  pi.style["background-repeat"] = "no-repeat";
  pi.style["background-position"] = "right top";
})
}

function createTinyImage (color) {
const canvas = document.createElement('canvas');
var ctx = canvas.getContext('2d');
canvas.width = 1;
canvas.height = 1;
ctx.fillStyle = color;
ctx.fillRect(0,0,1,1);
return canvas.toDataURL('image/png','');
} 

function questionSet () {
function getRandomInt(max) {
  return Math.floor(Math.random() * Math.floor(max));
}
const substitutes = document.querySelector('#substitutes').innerText;
const words = substitutes.split(/#+/).filter(x => x);
const wordSpan = document.querySelector('.question .word');
const word = wordSpan.innerText;
words.push(word);
const index = getRandomInt(words.length);
wordSpan.innerText = words[index];
}

function setRefDictLink () {
const links = document.querySelectorAll('.mac_dict a')
links.forEach(link => {
  link.classList.add('non_clickable')

  let href = link.href
  if (!href.includes('x-dictionary')) {
    return
  }
  const text = link.textContent
  link.href = 'mkdictionaries:///?text=' + text
})

}

function setHR () {
const divs = document.querySelectorAll('.mac_dict')
for (let i = 1; i < divs.length; i++) {
  const div = divs[i]
  const hr = document.createElement("hr")
  div.before(hr)
}
}

function setMemoClassOfJpNotes () {
const cardTypeSpan = document.querySelector('#card_type')
const deckNameSpan = document.querySelector('#deck_name')
const memoSpan = document.querySelector('.memo')
if (cardTypeSpan && cardTypeSpan.textContent == '日本語'
    && deckNameSpan && deckNameSpan.textContent == 'All::日本語'
    && memoSpan.textContent) {
  memoSpan.classList.add('decoration')
}
}

function make_links_clickable () {
document.querySelectorAll('.mac_dict a').forEach(a => {
  a.classList.remove('non_clickable')
})
}
