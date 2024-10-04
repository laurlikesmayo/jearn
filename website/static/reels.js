// Load the IFrame Player API code asynchronously.
let tag = document.createElement('script');
tag.src = "https://www.youtube.com/iframe_api";
let firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// Create an array to store YouTube player objects
let players = [];
console.log('js working');

// This function creates an <iframe> (and YouTube player) after the API code downloads.
function onYouTubeIframeAPIReady() {
    console.log('YouTube IFrame API ready');
    const iframes = document.querySelectorAll('iframe');

    // Clear previous players
    players = [];

    if (iframes.length > 0) {
        iframes.forEach((iframe, index) => {
            players[index] = new YT.Player(iframe.id, {
                events: {
                    'onStateChange': onPlayerStateChange
                }
            });
            console.log('iframe ready', iframe.id);
        });
    } else {
        console.log('No iframes found');
    }
}

// Listen for changes in player state
function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        players.forEach((player, index) => {
            if (player !== event.target) {
                player.pauseVideo();
            }
        });
    }
}

// Function to check which video is in view
function checkInView() {
    const navbarHeight = 59; // Height of your navbar in pixels
    const videoContainers = document.querySelectorAll('.video-container');
    videoContainers.forEach((container, index) => {
        const rect = container.getBoundingClientRect();
        if (rect.top >= navbarHeight && rect.bottom <= window.innerHeight) {
            players[index].playVideo();
        } else {
            players[index].pauseVideo();
        }
    });
}

// Add event listeners once
window.addEventListener('scroll', checkInView);
window.addEventListener('load', () => {
    checkInView(); // Check on load
    onYouTubeIframeAPIReady(); // Reinitialize players
});