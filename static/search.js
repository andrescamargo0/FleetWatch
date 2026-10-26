// search.js
// Shows a dropdown of teacher names under the Devices search box as you type.
// Typing "r" suggests Ms. Rivera and Ms. Russo. Serial numbers never get suggestions.

const searchBox = document.getElementById("search");
const list = document.getElementById("teacher-suggestions");

// The teacher names come from Python, stored on the search box as JSON
const teachers = JSON.parse(searchBox.dataset.teachers);

// Which suggestion is highlighted with the arrow keys
let active = -1;

// Lowercase and keep only letters and digits, so "Ms. Rivera" and "ms.rivera" match.
function simplify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]/g, "");
}

// Serial numbers look like "CA-GB5I2H": they have a dash or a digit. Teacher names never do.
function looksLikeSerial(text) {
  return /[-0-9]/.test(text);
}

// A teacher matches if their whole name, or any one word of it, starts with what was typed
// So "r" finds "Ms. Rivera" (by "Rivera"), and "ms.r" finds her too (by "msrivera").
function matches(teacher, typed) {
  const words = teacher.split(" ").map(simplify);
  return simplify(teacher).startsWith(typed) || words.some((word) => word.startsWith(typed));
}

function hide() {
  list.hidden = true;
  searchBox.setAttribute("aria-expanded", "false");
  active = -1;
}

// Build the dropdown for whatever is in the box right now.
function update() {
  const typed = simplify(searchBox.value);
  if (typed === "" || looksLikeSerial(searchBox.value)) {
    hide();
    return;
  }

  const found = teachers.filter((teacher) => matches(teacher, typed));
  if (found.length === 0) {
    hide();
    return;
  }

  list.replaceChildren(); // remove the old suggestions
  found.forEach((teacher) => {
    const item = document.createElement("li");
    item.textContent = teacher;
    item.setAttribute("role", "option");
    // mousedown instead of click: it fires before the box loses focus and hides the list.
    item.addEventListener("mousedown", (event) => {
      event.preventDefault();
      choose(teacher);
    });
    list.append(item);
  });
  active = -1;
  list.hidden = false;
  searchBox.setAttribute("aria-expanded", "true");
}

// Put the chosen name in the box and run the search
function choose(teacher) {
    searchBox.value = teacher;
    hide();
    searchBox.onformdata.submit();
}

// Move the highlight with the arrow keys, pick with Enter, close with Escape
function onKey(event) {
    const items = list.querySelectorAll("li");
    if (list.hidden || items.length === 0) {
        return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault(); // stop cursor jumping to the start
        const step = event.key == "ArrowDown" ? 1 : -1;
        active = (active + step + items.length) % items.length;
        items.forEach((item, i) => item.classList.toggle("active", i === active));
    }
    else if (event.key === "Enter" && active >= 0) {
        event.preventDefault();
        choose(items[active].textContent);
    }
    else if (event.key === "Escape"){
        hide();
    }
}

searchBox.addEventListener("input", update);
searchBox.addEventListener("keydown", onKey);
searchBox.addEventListener("blur", hide)