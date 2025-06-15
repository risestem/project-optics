// Array of random video URLs for demo purposes
const demoVideos = [
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4'
];

// Get DOM elements
const promptForm = document.getElementById('promptForm');
const promptInput = document.getElementById('promptInput');
const resultVideo = document.getElementById('resultVideo');

// Function to get random video
function getRandomVideo() {
  const randomIndex = Math.floor(Math.random() * demoVideos.length);
  return demoVideos[randomIndex];
}

// Function to play random video
function playRandomVideo() {
  const randomVideoUrl = getRandomVideo();
  resultVideo.src = randomVideoUrl;
  resultVideo.style.display = 'block';
  resultVideo.play();
  
  // Clear the input and remove focus to trigger fade away
  promptInput.value = '';
  promptInput.blur();
  
  // Also blur any focused element within the form (like the button)
  if (document.activeElement && promptForm.contains(document.activeElement)) {
    document.activeElement.blur();
  }
  
  // Add the video-playing class after removing all focus
  promptForm.classList.add('video-playing');
  
  // Focus the video element for better UX (allows keyboard controls)
  resultVideo.focus();
  
  // Optional: Log which video is playing for debugging
  console.log('Playing video:', randomVideoUrl);
}

// Handle video end event to remove the class
resultVideo.addEventListener('ended', function() {
  promptForm.classList.remove('video-playing');
  // Auto-focus back to input when video ends
  promptInput.focus();
});

// Optional: Handle video pause/stop events
resultVideo.addEventListener('pause', function() {
  // Only remove class if video actually ended, not just paused
  if (resultVideo.ended) {
    promptForm.classList.remove('video-playing');
    promptInput.focus();
  }
});

// Handle form submission
promptForm.addEventListener('submit', function(e) {
  e.preventDefault(); // Prevent form from actually submitting
  
  const prompt = promptInput.value.trim();
  
  if (prompt) {
    // Play a random video (this will clear the input)
    playRandomVideo();
  }
});

// Optional: Handle Enter key in input field
promptInput.addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    e.preventDefault();
    promptForm.dispatchEvent(new Event('submit'));
  }
});

// Auto-focus the input when the page loads
window.addEventListener('load', function() {
  promptInput.focus();
});