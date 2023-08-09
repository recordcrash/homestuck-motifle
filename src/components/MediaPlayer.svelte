<script>
import { onMount } from 'svelte';

export let game;

let player; // YouTube or SoundCloud player instance
let soundcloudPlayer; // SoundCloud player instance
let isPlaying = false;

onMount(() => {
    setupYouTubePlayer();
    setupSoundCloudPlayer();
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
}

function togglePlay() {
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
}


function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.ENDED) {
        isPlaying = false;
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
</script>

<div id="player-container">
    <div id="youtube-player"></div>
    <iframe id="soundcloud-player" src="" frameborder="0"></iframe>
    
    <button class="play-button" on:click={togglePlay}>
        {isPlaying ? '⏸' : '▶'}
    </button>
    <button class="stop-button" on:click={stopSong}>
        ⏹
    </button>
</div>

<style>
    #youtube-player,
    #soundcloud-player {
        display: none;
    }

    .play-button {
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
        margin: 0 0 0 5px;
        transition: background-color 0.3s;
    }

    .play-button:hover {
        background-color: #d32f2f;
    }

    .play-button:focus {
        outline: none;
    }

    .stop-button {
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
        margin: 0 5px 0 0 ;
        transition: background-color 0.3s;
    }

    .stop-button:hover {
        background-color: #d32f2f;
    }

    .stop-button:focus {
        outline: none;
    }
</style>
