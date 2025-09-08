// submit the form and trigger the bell sound on clicking the "Fight!" button
function bellSoundSubmit() {
    // define the forma and bell sound as constants
    const bell = document.getElementById('ding-ding');
    const form = document.querySelector('form');

    // if there is no bell or form present, submit the form
    if (!bell || !form) {
        if (form) form.submit();
        return;
    }

    // reset bell sound to time = 0
    bell.pause();
    bell.currentTime = 0;
    bell.play().then(() => {
        // delay the form submission by 2 seconds for the bell to play
        setTimeout(() => {
            form.submit();
        }, 2000);
        }).catch(() => {
        // if bell fails, submit form anyway
        form.submit();
    });
}

// Triggered when a dropdown changes
function fetchBoxer(selectId, photoId, aliasId, heightId, reachId, stanceId, eraId, winsId, lossesId, ko_ratioId, win_ratioId, ) {
    let select = document.getElementById(selectId);
    let boxerId = select.value;

  // if there is no boxer ID available, abandon the operation
  if (!boxerId) return;

  // trigger the API call for the boxer attributes, parsing in the ID of the selected boxer
  let request = new XMLHttpRequest();
  request.open("GET", "/api/boxer/" + boxerId, true);

  // if the request is successful, update the DOM with the attributes
  request.onload = function() {
      if (request.status === 200) {
          let boxer = JSON.parse(request.responseText);

              document.getElementById(photoId).src = boxer.photo;
              document.getElementById(aliasId).textContent = boxer.alias || "";
              document.getElementById(heightId).textContent = "Height: " + (boxer.height_cm || "--") + " cm";
              document.getElementById(reachId).textContent = "Reach: " + (boxer.reach_cm || "--") + " cm";
              document.getElementById(stanceId).textContent = "Stance: " + (boxer.stance || "--");
              document.getElementById(ko_ratioId).textContent = "Ko Ratio: " + (boxer.ko_ratio || "--")
              document.getElementById(win_ratioId).textContent = "Win Ratio: " + (boxer.win_ratio || "--")
              document.getElementById(winsId).textContent = "Wins: " + (boxer.wins || "--")
              document.getElementById(lossesId).textContent = "Losses: " + (boxer.losses || "--")
              document.getElementById(eraId).textContent = "Eras: " + (boxer.eras || "--")
    }
  };

  request.send();
}

// Attach event listeners to both of the dropdown boxes when the page is loaded
window.onload = function() {
    let fighter1 = document.getElementById("fighter1-select");
    let fighter2 = document.getElementById("fighter2-select");

        // attachment for fighter 1 dropdown
        if (fighter1) {
            fighter1.addEventListener("change", function() {
            fetchBoxer("fighter1-select", "fighter1-photo", "fighter1-alias", "fighter1-height", "fighter1-reach", "fighter1-stance", "fighter1-eras", "fighter1-wins", "fighter1-losses");
            });
        }

        // attachment for fighter 1 dropdown
        if (fighter2) {
            fighter2.addEventListener("change", function() {
            fetchBoxer("fighter2-select", "fighter2-photo", "fighter2-alias", "fighter2-height", "fighter2-reach", "fighter2-stance", "fighter2-eras", "fighter2-wins", "fighter2-losses");
            });
        }
};



<!-- SCRAPPED: run glove touch animation and lets-rumble sound, then transition to results page after an 8-second delay -->
function gloveTouch() {
    const rumble = document.getElementById('lets-rumble');

    window.addEventListener("DOMContentLoaded", () => {
        document.getElementById("lets-rumble").play();
        setTimeout(() => {
            window.location.href = "{{ url_for('main.results') }}";
            }, 8000);
    });
}
