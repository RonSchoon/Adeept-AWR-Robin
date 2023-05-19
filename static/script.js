const txt = document.getElementById('result');

function fetchCommand(command, params) {
    data = new FormData();
	data.append('action', command);
	if (typeof params !== "undefined") {
		data.append('params', params);
	}
    fetch('/', {
        method : 'POST',
        body : data
    })
    .then(function(response) {
        if(response.ok) {
            response.text().then(function(text) {
                if (command == 'info') {
                  document.getElementById('status').innerHTML = text;
                } else {
                  txt.innerHTML = text;
                }
            });
        }
        else {
            throw Error('Something went wrong');
        }
    })
	return false;  
}

function info() {
  fetchCommand('info');
}

function isTouchEnabled() {
    return ( 'ontouchstart' in window );
}

///////////
// Helpers
// adds left mouse button down and up handlers for given html button ids
// function... provides the funtion to call. If null, no handler will be added for this mouse event
function addEventListenerDownUp(id, functionDown, functionUp, params) {
    let element = document.getElementById(id);
    if (element !== null) {
        if (isTouchEnabled()) {
            if (functionDown !== null) {
				if (typeof params !== "undefined") {
					element.addEventListener("touchstart", fetchCommand(functionDown, document.getElementById("favcolor").value));
				} else {
					element.addEventListener("touchstart", fetchCommand(functionDown));
				}
            }
            if (functionUp !== null) {
                element.addEventListener("touchend", fetchCommand(functionUp));
            }
        } else {
            if (functionDown !== null) {
				if (typeof params !== "undefined") {
					element.addEventListener("mousedown", event => {
						if (event.button == 0) {
							fetchCommand(functionDown, document.getElementById("favcolor").value);
						}
					});
				} else {
					element.addEventListener("mousedown", event => {
						if (event.button == 0) {
							fetchCommand(functionDown);
						}
					});
				}
            }
            if (functionUp !== null) {
                element.addEventListener("mouseup", event => {
                    if (event.button == 0) {
                        fetchCommand(functionUp);
                    }
                });
            }
        }
    } else {
        alert("Please check your html page. There is no element with id: " + id + "! Any typo?");
    }
}

function joyRiding() {
      joyDirection = document.getElementById('joy1Direzione').value;
      switch (joyDirection) {
        case 'N':
          fetchCommand('forward');
          break;
        case 'S':
          fetchCommand('backward');
          break;
        case 'W':
          fetchCommand('left');
          break;
        case 'E':
          fetchCommand('right');
          break;
        default: // joyDirection = 'C'
          fetchCommand('DS');
      }
}

// camera
addEventListenerDownUp('btnCamUp', 'camUp', null);
addEventListenerDownUp('btnCamDown', 'camDown', null);
// drive control
addEventListenerDownUp('btnDCForward', 'forward', 'DS');
addEventListenerDownUp('btnDCBackward', 'backward', 'DS');
addEventListenerDownUp('btnDCLeft', 'left', 'TS');
addEventListenerDownUp('btnDCRight', 'right', 'TS');
// Joystick
var joy1IinputPosX = document.getElementById("joy1PosizioneX");
var joy1InputPosY = document.getElementById("joy1PosizioneY");
var joy1Direzione = document.getElementById("joy1Direzione");
var joy1X = document.getElementById("joy1X");
var joy1Y = document.getElementById("joy1Y");

var Joy1 = new JoyStick('joy1Div', {}, function(stickData) {
  joy1IinputPosX.value = stickData.xPosition;
  joy1InputPosY.value = stickData.yPosition;
  joy1Direzione.value = stickData.cardinalDirection;
  joy1X.value = stickData.x;
  joy1Y.value = stickData.y;
});

if(isTouchEnabled()) {
  document.addEventListener("touchmove", joyRiding, false);
  document.getElementById('joy1Div').addEventListener("touchend", fetchCommand('DS'));
} else {
  document.addEventListener("mousemove", joyRiding, false);
}
// actions
addEventListenerDownUp('btnGreen', 'green', 'policeOff');
addEventListenerDownUp('btnColor', 'color', 'policeOff', document.getElementById("favcolor").value);
addEventListenerDownUp('btnPolice', 'police', null);
addEventListenerDownUp('btnPoliceOff', 'policeOff', null);
addEventListenerDownUp('btndetectFaces', 'detectFaces', null);
addEventListenerDownUp('btndetectFacesOff', 'detectFacesOff', null);
addEventListenerDownUp('btnWatchdog', 'watchdog', null);
addEventListenerDownUp('btnWatchdogOff', 'watchdogOff', null);
addEventListenerDownUp('btnAutopilot', 'autopilot', null);
addEventListenerDownUp('btnAutopilotOff', 'autopilotOff', null);
addEventListenerDownUp('btnPowerLow', 'powerLow', null);
addEventListenerDownUp('btnPowerDefault', 'powerDefault', null);
// request robot status every 5 secs.
setInterval(info, 1000);