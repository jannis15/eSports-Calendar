const EventPriority = {
  Standard: 'standard',
  NoTime: 'notime',
  Uncertain: 'uncertain',
  Certain: 'certain',
};
function GetEventPriorityColor(eventPriority) {
  switch (eventPriority) {
    case EventPriority.Standard:
      return '#edf0f3';
    case EventPriority.NoTime:
      return '#cc343e';
    case EventPriority.Uncertain:
      return '#efb700';
    case EventPriority.Certain:
      return '#008450';
    default:
      return '#edf0f3';
    }
};

function handleEventPriorityButtonClick(eventPriority) {
  if (currentButton) {
    currentButton.classList.remove('pressed');
  }
  currentButton = controlsEl.querySelector(`.${eventPriority}`);
  currentButton.classList.add('pressed');

  currentEventPriority = eventPriority;
  currentEventPriorityColor = GetEventPriorityColor(currentEventPriority);
};

function calendarInit() {
  const headerEl = document.querySelector('.fc-header-toolbar.fc-toolbar.fc-toolbar-ltr');

  // generate the event priority buttons
  buttons.forEach((button) => {
    const buttonEl = document.createElement('button');
    buttonEl.classList.add(button.className);
    buttonEl.classList.add('event-priority-button', 'outline'); 

    const iconEl = document.createElement('img');
    iconEl.src = button.iconUrl;
    iconEl.classList.add('event-priority-button-icon');
    buttonEl.appendChild(iconEl);

    const textEl = document.createElement('span');
    textEl.textContent = button.text;
    buttonEl.appendChild(textEl);

    buttonEl.addEventListener('click', button.click);
    buttonEl.setAttribute('aria-pressed', 'false'); 
    controlsEl.appendChild(buttonEl);
  });

  // insert the buttons before the parent of the header element
  if (headerEl && controlsEl) {
    const parentEl = headerEl.parentNode;
    parentEl.insertBefore(controlsEl, headerEl.nextSibling);
  }

  handleEventPriorityButtonClick(EventPriority.Standard);
};

function getContrastColor(givenColor) {
  const darkColor = '#171616';
  const lightColor = '#e8e9e9';
  const rgbGivenColor = convertToRGB(givenColor);
  const rgbDarkColor = convertToRGB(darkColor);
  const rgbLightColor = convertToRGB(lightColor); 
  const contrastWithDark = calculateContrastRatio(rgbDarkColor, rgbGivenColor);
  const contrastWithLight = calculateContrastRatio(rgbLightColor, rgbGivenColor);
  if (contrastWithDark > contrastWithLight) {
    return darkColor; 
  } else {
    return lightColor; 
  }
}

function convertToRGB(color) {
  const r = parseInt(color.substring(1, 3), 16);
  const g = parseInt(color.substring(3, 5), 16);
  const b = parseInt(color.substring(5, 7), 16);
  return { r, g, b }; 
}

function calculateContrastRatio(color1, color2) {
  const luminance1 = calculateLuminance(color1);
  const luminance2 = calculateLuminance(color2);
  return Math.abs(luminance1 - luminance2);
}

function calculateLuminance(color) {
  const { r, g, b } = color;

  const normalizedR = r / 255;
  const normalizedG = g / 255;
  const normalizedB = b / 255;

  const luminance = (0.2126*normalizedR) + (0.7152*normalizedG) + (0.0722*normalizedB);
  return luminance;
}

function getSRGBValue(color) {
  const sRGBValue = color / 255;
  return sRGBValue;
}

function formatDateDDMMYYYY(dateStr) {
  const [datePart] = dateStr.split(' ');
  const [year, month, day] = datePart.split('-');

  return `${day}.${month}.${year}`;
}