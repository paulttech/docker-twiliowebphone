function isContainerCreatedForToday(containers) {
  const currentDate = moment().format('YYYY-MM-DD');

  return containers.some(container => container.dataset.date === currentDate);
}

// Function to create a new small container
function createSmallContainer() {
  const container = document.createElement("div");
  container.style.width = "200px";
  container.style.height = "421px";
  container.style.border = "1px solid #2C2E45";
  container.style.display = "inline-block";
  const currentDate = moment().format('YYYY-MM-DD');
  container.dataset.date = currentDate;

  // Create elements inside the container
  const dayElement = document.createElement("span");
  dayElement.textContent = moment().format('dddd'); // Display the current day
  dayElement.style.color = "#CCCCCC";
  container.appendChild(dayElement);

  const dateElement = document.createElement("span");
  dateElement.style.fontSize = "x-large";
  dateElement.textContent = moment().format('Do'); // Display the current date
  dateElement.style.color = "#CCCCCC";
  container.appendChild(dateElement);

  const innerContainer = document.createElement("div");
  innerContainer.style.width = "197px";
  innerContainer.style.border = "1px solid #2C2E45";
  innerContainer.style.marginTop = "10px";
  container.appendChild(innerContainer);

  const textElement = document.createElement("div");
  textElement.textContent = "hi";
  container.appendChild(textElement);

  return container;
}

// Function to initialize small containers
function initializeContainers() {
  const containerWrapper = document.getElementById("small-container-inside-recent-container");
  const containers = containerWrapper.querySelectorAll("div");

  if (!isContainerCreatedForToday([...containers])) {
    const newContainer = createSmallContainer();
    containerWrapper.appendChild(newContainer);
  }
}

// Initialize small containers on page load
initializeContainers();
