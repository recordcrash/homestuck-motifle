<script>
import { onDestroy, onMount } from 'svelte';

export let game;

let player; // YouTube or SoundCloud player instance
let soundcloudPlayer; // SoundCloud player instance
let isPlaying = false;
let isReady = false; // Whether the player is ready to play
let currentProgress = 0; // This value will keep track of the current playback progress
let currentTime = '00:00'; // This value will keep track of the current playback time
let seekBarInterval; // Interval to update the seek bar
let seekBarDisabled = true; // Whether the seek bar should be disabled

onMount(() => {
    setupYouTubePlayer();
    setupSoundCloudPlayer();
    seekBarInterval = setInterval(updateSeekBar, 500); // Update every half second
});

onDestroy(() => {
    clearInterval(seekBarInterval);
});

$: if (player) {
    if (game.song.urlType === 'youtube' && player.loadVideoById) {
        try {
            player.cueVideoById(extractYouTubeID(game.song.url));
        } catch (error) {
            console.error("Error loading video:", error);
        }
    } else if (game.song.urlType === 'soundcloud' && soundcloudPlayer) {
        soundcloudPlayer.load(game.song.url);
    }
}

$: {
    if (game) {
        resetPlayerState();
    }
}

function onPlayerReady(event) {
    isReady = true;
    console.log("YouTube Player is ready.");

    if (game && game.song.urlType === 'youtube') {
        try {
            event.target.cueVideoById(extractYouTubeID(game.song.url));
        } catch (error) {
            console.error("Error loading video:", error);
        }
    }
}

function resetPlayerState() {
    if (game.song.urlType === 'youtube' && player && player.stopVideo) {
        player.stopVideo();
    } else if (game.song.urlType === 'soundcloud' && soundcloudPlayer) {
        soundcloudPlayer.pause();
    }
    isPlaying = false;
    currentProgress = 0;
}

function stopSong() {
    if (game.song.urlType === 'youtube' && player && player.stopVideo) {
        console.log('Stopping YouTube video');
        player.stopVideo();
    } else if (game.song.urlType === 'soundcloud' && soundcloudPlayer) {
        console.log('Stopping SoundCloud track');
        soundcloudPlayer.seekTo(0); // Reset SoundCloud track to start
        soundcloudPlayer.pause();   // Ensure SoundCloud track is paused
    }
    isPlaying = false;
    currentProgress = 0;
    currentTime = '00:00';
    seekBarDisabled = true;
}

function togglePlay() {
    if (!isReady) return;
    seekBarDisabled = false;
    isPlaying = !isPlaying;
    console.log('Toggling play', isPlaying);
    if (isPlaying) {
        console.log('Playing song', game.song);
        if (game.song.urlType === 'youtube') {
            if (player && player.playVideo) {
                console.log('Playing YouTube video');
                player.playVideo();
            } else {
                console.log('YouTube player not ready yet');
            }
        } else if (game.song.urlType === 'soundcloud') {
            if (soundcloudPlayer) {
                console.log('Playing SoundCloud track');
                soundcloudPlayer.play();
            } else {
                console.log('SoundCloud player not ready yet');
            }
        }
    } else {
        if (game.song.urlType === 'youtube' && player && player.pauseVideo) {
            console.log('Pausing YouTube video');
            player.pauseVideo();
        } else if (game.song.urlType === 'soundcloud' && soundcloudPlayer) {
            console.log('Pausing SoundCloud track');
            soundcloudPlayer.pause();
        }
    }
}

function setupYouTubePlayer() {
    const initializePlayer = () => {
        player = new YT.Player('youtube-player', {
            videoId: extractYouTubeID(game.song.url),
            events: {
                'onReady': onPlayerReady,
                'onStateChange': onPlayerStateChange
            }
        });
    };

    if (window.YT && window.YT.Player) {
        // If YT API is already loaded, initialize the player immediately
        initializePlayer();
    } else {
        // If YT API is not loaded yet, set the callback to initialize the player
        window.onYouTubeIframeAPIReady = initializePlayer;
    }
}

function setupSoundCloudPlayer() {
    const soundCloudIframe = document.getElementById('soundcloud-player');
    const soundCloudURL = game.song.urlType === 'soundcloud' ? game.song.url : 'https://soundcloud.com/romm_music/beta-version-rom-m';
    soundCloudIframe.setAttribute('src', `https://w.soundcloud.com/player/?url=${encodeURIComponent(soundCloudURL)}`);
    soundcloudPlayer = SC.Widget(soundCloudIframe);
    soundcloudPlayer.bind(SC.Widget.Events.READY, () => {
        console.log('SoundCloud player is ready.');
        isReady = true;
    });
    soundcloudPlayer.bind(SC.Widget.Events.FINISH, () => {
        console.log('SoundCloud track finished.');
        isPlaying = false;
        currentProgress = 0; // Reset the progress bar
        currentTime = '00:00'; // Reset the timestamp
        seekBarDisabled = true;
    });
}


function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.ENDED) {
        isPlaying = false;
        currentProgress = 0; // Reset the progress bar
        currentTime = '00:00'; // Reset the timestamp
        seekBarDisabled = true;
    }
}

function extractYouTubeID(url) {
    let videoId;
    const match = url.match(/(youtube\.com\/watch\?v=|youtu.be\/)([a-zA-Z0-9_-]+)/);
    if (match) {
        videoId = match[2];
    }
    return videoId;
}

const updateSeekBar = () => {
    if (isPlaying) {
        if (game.song.urlType === 'youtube' && player && player.getDuration) {
            const percentage = (player.getCurrentTime() / player.getDuration()) * 100;
            currentProgress = percentage || 0;
            currentTime = formatTime(player.getCurrentTime());
        } else if (game.song.urlType === 'soundcloud' && soundcloudPlayer) {
            soundcloudPlayer.getPosition(position => {
                soundcloudPlayer.getDuration(duration => {
                    const percentage = (position / duration) * 100;
                    currentProgress = percentage || 0;
                    // Soundcloud provides the position in milliseconds
                    currentTime = formatTime(position / 1000);
                });
            });
        }
    }
}

const handleSeekBarChange = event => {
    const percentage = event.target.value;
    
    if (game.song.urlType === 'youtube' && player && player.getDuration) {
        const goToTime = (percentage / 100) * player.getDuration();
        player.seekTo(goToTime);
    } else if (game.song.urlType === 'soundcloud' && soundcloudPlayer) {
        soundcloudPlayer.getDuration(duration => {
            const goToTime = (percentage / 100) * duration;
            soundcloudPlayer.seekTo(goToTime);
        });
    }
}

const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};
</script>

<div id="player-container">
    <div id="youtube-player"></div>
    <iframe id="soundcloud-player" src="" frameborder="0" title="soundcloud"></iframe>
    
    <div class="controls-container">
        <button class="play-button" on:click={togglePlay} disabled={!isReady}>
            {isReady ? (isPlaying ? '⏸' : '▶') : '⧗'}
        </button>
        
        <div class="seek-bar-container">
            <input 
                type="range" 
                class="seek-bar" 
                min="0" 
                max="100" 
                value={currentProgress} 
                disabled={seekBarDisabled}
                on:input={handleSeekBarChange}
            />
            <div class="time-display">
                <span class="timestamp-pill">{currentTime}</span>
            </div>
        </div>

        <button class="stop-button" on:click={stopSong} disabled={!isReady}>
            { isReady ? '⏹' : '⧗'}
        </button>
    </div>
</div>


<style>
    #youtube-player,
    #soundcloud-player {
        display: none;
    }

    .play-button, .stop-button {
        background-color: var(--color-theme-1);
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
        font-size: 20px;
        line-height: 40px;
        text-align: center;
        transition: background-color 0.3s;
    }

    .play-button:hover, .stop-button:hover {
        background-color: #d32f2f;
    }

    .play-button:focus, .stop-button:focus {
        outline: none;
    }

    .play-button:disabled, .stop-button:disabled, .play-button:disabled:hover, .stop-button:disabled:hover {
        cursor: not-allowed;
        opacity: 0.5;
    }

    .play-button {
        margin-left: 5px;
        margin-right: 5px;
    }

    .stop-button {
        margin-left: 5px;
        margin-right: 5px;
    }

    #player-container {
        position: relative;
        width: 100%;
    }

    .controls-container {
        position: relative;
        display: flex;
        align-items: center; /* To vertically align the buttons and SVG */
        justify-content: space-between; /* To spread out the two buttons */
        width: 100%;
        height: 50px;
    }

    .play-button, .stop-button {
        position: relative; /* Relative to ensure z-index stacking order is respected */
        z-index: 2; /* Ensuring buttons are over the SVG */
    }

    .seek-bar-container {
        width: calc(100% - 150px);
        margin-top: 10px; /* provide some space between the buttons and the seek bar */
    }

    .seek-bar {
        width: 100%;
        appearance: none; /* removes default appearance */
        height: 20px;
        border-radius: 10px;
        background: #ffffff;
        outline: none;
        transition: opacity 0.2s;
        cursor: pointer;
    }

    .seek-bar::-webkit-slider-thumb {
        appearance: none;
        width: 25px;
        height: 25px;
        border-radius: 50%;
        background: var(--color-theme-1);
        cursor: pointer;
        transition: background 0.2s;
    }

    .seek-bar::-moz-range-thumb {
        width: 25px;
        height: 25px;
        border-radius: 50%;
        background: var(--color-theme-1);
        cursor: pointer;
        transition: background 0.2s;
    }

    .seek-bar::-webkit-slider-thumb:hover,
    .seek-bar::-moz-range-thumb:hover {
        background: #d32f2f;
    }

    .seek-bar::-webkit-slider-runnable-track,
    .seek-bar::-moz-range-track {
        width: 100%;
        height: 4px;
        cursor: pointer;
        border-radius: 2px;
        background: #ffffff;
    }

    .time-display {
        text-align: center;
        font-size: 12px;
        color: #555;    /* darker color for better visibility */
    }

    .timestamp-pill {
        display: inline-block;
        background-color: white;
        border-radius: 15px;   /* Gives it a rounded pill shape */
        padding: 2px 8px;      /* Add some padding for aesthetics */
        font-size: 12px;       /* Adjust to the desired font size */
        color: #333;           /* Text color */
    }
</style>
