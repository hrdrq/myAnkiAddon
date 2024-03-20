const TYPE_TEXT = 3;
function highlight(element, regex, className) {
    var document = element.ownerDocument;
    
    var nodes = [],
        text = "",
        node,
        nodeIterator = document.createNodeIterator(element, NodeFilter.SHOW_TEXT, null, false);
        
    while ((node = nodeIterator.nextNode())) {
        nodes.push({
            textNode: node,
            start: text.length
        });
        text += node.nodeValue
    }
    
    // console.log("yyy", nodes.length)
    if (!nodes.length)
        return;

    
    var match;
    while ((match = regex.exec(text))) {
        var matchLength = match[0].length;
        
        // Prevent empty matches causing infinite loops        
        if (!matchLength)
        {
            regex.lastIndex++;
            continue;
        }
        
        for (var i = 0; i < nodes.length; ++i) {
            node = nodes[i];
            var nodeLength = node.textNode.nodeValue.length;
            
            // Skip nodes before the match
            if (node.start + nodeLength <= match.index)
                continue;
        
            // Break after the match
            if (node.start >= match.index + matchLength)
                break;
            
            // Split the start node if required
            if (node.start < match.index) {
                nodes.splice(i + 1, 0, {
                    textNode: node.textNode.splitText(match.index - node.start),
                    start: match.index
                });
                continue;
            }
            
            // Split the end node if required
            if (node.start + nodeLength > match.index + matchLength) {
                nodes.splice(i + 1, 0, {
                    textNode: node.textNode.splitText(match.index + matchLength - node.start),
                    start: match.index + matchLength
                });
            }
            // console.log("xxxx")
            // Highlight the current node
            var spanNode = document.createElement("span");
            spanNode.className = className;
            // if (className == 'not_example') {
            //     console.log(node.textNode)
            // }
            
            // console.log(node)
            // console.log(node.textNode.parentNode)
            // console.log(spanNode)
            node.textNode.parentNode.replaceChild(spanNode, node.textNode);
            spanNode.appendChild(node.textNode);
        }
    }
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
    const div = document.createElement("div");
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
  const BORDER = "solid 0.12em";
  document.querySelectorAll(".pitch .flat").forEach(pi => {
    pi.style["border-top"] = BORDER;
  })
  document.querySelectorAll(".pitch .descent").forEach(pi => {
    const color = window.getComputedStyle(pi).color;
    const tinyImage = createTinyImage(color);
    pi.style["border-top"] = BORDER;
    pi.style["background-image"] = `url("${tinyImage}")`;
    pi.style["background-size"] = "0.12em 0.36em";
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

function main () {
    pitch();
    document.querySelectorAll('.meaning').forEach(dm => {
      if (dm.querySelector('.mac_dict')) return;
      // console.log(dm)
      highlight(dm, new RegExp("〔.*?〕", "g"), "note");
      highlight(dm, new RegExp("《.*?》", "g"), "quote");
      highlight(dm, new RegExp("〘.*?〙", "g"), "category");
      highlight(dm, new RegExp("[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲㋐㋑㋒㋓㋔㋕㋖㋗㋘㋙❶❷❸❹❺❻]", "g"), "number");
      highlight(dm, new RegExp("「.*?」", "g"), "example");
      highlight(dm, new RegExp("［[0-9]］", "g"), "pron");
      highlight(dm, new RegExp("（ ?[動|形|副|名|接尾|連語|トタル|補助動詞].*?）", "g"), "speech");
    //   highlight(dm, new RegExp("［(可能|慣用|表記|派生|句)］.+$", "g"), "grammar");
      highlight(dm, new RegExp("▽↔ (.*?)([^ ]+)", "g"), "derivative");
      highlight(dm, new RegExp("［季］[ +](春|夏|秋|冬|新年)。?", "g"), "season");
      dm.querySelectorAll(".example").forEach(ex => {
        // if (ex.nextSibling && ex.nextSibling.nodeType === TYPE_TEXT) {
        //   if (ex.nextSibling.data.match(/^(の)/g)) {
        //     ex.classList.remove("example");
        //     return;
        //   }
        // }

        // if (ex.parentNode.textContent.match(/「.*?」[の|と|を|に|より|など]/g)) {
        //     ex.
        // }

        highlight(ex.parentNode, new RegExp("「[^「]+?」[の|と|を|に|より|など|は]", "g"), "not_example");
        if (!ex.parentNode.querySelector('.source')) {
          highlight(ex.parentNode, new RegExp("／.*?(?=」)", "g"), "source");
        }


        // if (ex.parentNode.style.fontSize) {
        //   ex.classList.add("source");
        // }
        // console.log("x", ex.parentNode.style.fontSize)
      });
      dm.querySelectorAll(".speech").forEach(sp => {
        let node = sp.nextSibling;
        while (node) {
          // console.log(node.style.fontSize)
          if (node.nodeType === TYPE_TEXT) {
            const spanNode = document.createElement("span");
            spanNode.className = "speech_sub";
            node.parentNode.replaceChild(spanNode, node);
            spanNode.append(node);
            node = spanNode;
          } else if (node.style && node.style.fontSize) {
            node.classList.add("speech_sub")
          }
          node = node.nextSibling;
        }
      })
      // dm.querySelectorAll("span, div").forEach(sd => {
      //   // const firstChild = sp.firstChild;
      //   // console.log(firstChild)
      //   // if (firstChild === TYPE_TEXT) {
      //   //   console.log(firstChild.data)
      //   // }
      //   sd.children.forEach(ch => {
      //     // console.log(ch)
      //     // console.log(ch == TYPE_TEXT)
      //     console.log("x", ch)
      //     if (ch === TYPE_TEXT) {
      //       console.log(ch)
      //     }
      //     if (ch === TYPE_TEXT && ch.data.match(/[一二]/g)) {
      //       sd.classList.add("number");
      //     }
      //   })
      // })
      const nodeIterator = document.createNodeIterator(dm, NodeFilter.SHOW_TEXT, null, false);
      let node, nodes = [];
      while ((node = nodeIterator.nextNode())) {
        nodes.push(node);
      }
      nodes.forEach(node => {
        if (node.data.match(/^[一二三四五六七八九十]$/g)) {
          const spanNode = document.createElement("span");
          spanNode.className = "number";
          node.parentNode.replaceChild(spanNode, node);
          spanNode.append(node);
        } else if (node.data.match(/［(可能|慣用|表記|派生|句)］/g)) {
            const grandParent = node.parentNode.parentNode;
            grandParent.classList.add("grammar")
            if (grandParent.style.float) {
                grandParent.parentNode.classList.add("grammar");
            }
        //   const spanNode = document.createElement("span");
        //   spanNode.className = "grammar";
        //   node.parentNode.parentNode.replaceChild(spanNode, node);
        //   spanNode.append(node);
    //   highlight(dm, new RegExp("［(可能|慣用|表記|派生|句)］.+$", "g"), "grammar");

        }
      })
      // dm.querySelectorAll('*').forEach(el => {
      //   el.childNodes.forEach(ch => {
      //     if (ch.nodeType === TYPE_TEXT) {
      //       ch.remove()
      //       // console.log(ch);
      //       // ch.nodeValue = '<div class="number">' + ch.nodeValue + '</div>';
      //       // console.log(ch.nodeValue);
      //     }
      //   })
      //   // console.log(el.childNodes);
      // })
      // console.log(dm.querySelectorAll('*'))
    });

    setHR()
    // setDictLink()
    setRefDictLink()
}

function questionSet () {
  function getRandomInt(max) {
    return Math.floor(Math.random() * Math.floor(max));
  }
  const substitutes = document.querySelector('#substitutes').innerText;
  const words = substitutes.split(/#+/).filter(x => x);
  const wordSpan = document.querySelector('.question_word');
  const word = wordSpan.innerText;
  words.push(word);
  const index = getRandomInt(words.length);
  wordSpan.innerText = words[index];
}

function setDictLink () {
  const isIphone = navigator.userAgent.indexOf('iPhone') > 0
  const element = document.querySelector('#dict_link')
  const data = element.attributes['data-text'].value
  if (isIphone) {
    element.href = 'mkdictionaries:///?text=' + data
  } else {
    element.href = 'dict://' + data
  }
}

function setRefDictLink () {
  const links = document.querySelectorAll('a')
  links.forEach(link => {
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