<script>
    import { slide } from 'svelte/transition';
    import { onMount } from 'svelte';

    export let game;

    let countdownTime;
    let isCurrentGame;
    let artistsHTML = '';

    const rarityEmojis = {
        // 🟫🟨🟩🟦🟪 from common to rare
        5: '🟫',
        4: '🟨',
        3: '🟩',
        2: '🟦',
        1: '🟪',
    }
    
    onMount(() => {
        // we want to be consistent with the game's date, and not the user's timezone
        // so we will use UTC midnight
        // additionally, countDownTime is a human readable string like "in 5 minutes" or "in 2 hours, 30 minutes"
        countdownTime = getHumanReadableUntilMidnightString();
        // we also don't want to show the time left if we're showing a past game
        isCurrentGame = getIsCurrentGame();
        artistsHTML = getArtistsHTML();
    });

    // also update on game change
    $: if (game) {
        countdownTime = getHumanReadableUntilMidnightString();
        isCurrentGame = getIsCurrentGame();
    }

    function getIsCurrentGame() {
        // uses the game's dateString (UTC based, with midnight time) to check if we're looking at an old game
        // an old game is described as a game that happened 24 hours ago or more
        // gameDate needs to be UTC
        const gameDate = new Date(game.dateString);
        const now = new Date();
        const utcMidnight = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
        const utcMidnightMs = utcMidnight.getTime();
        const gameDateMs = gameDate.getTime();
        const isCurrentGame = gameDateMs >= utcMidnightMs;
        return isCurrentGame;
    }

    function deSlugify(artistName) {
        // to provide human readable artist names, we turn the - in to spaces
        // and capitalize the first letter of each word
        const artistNameWords = artistName.split('-');
        const artistNameWordsCapitalized = artistNameWords.map((word) => {
            return word.charAt(0).toUpperCase() + word.slice(1);
        });
        const artistNameCapitalized = artistNameWordsCapitalized.join(' ');
        return artistNameCapitalized;
    }

    function getArtistsHTML() {
        // an array of artist slugs comes in the game object, in its 'artist' property
        // we need to remove the 'artist:' part of each slug, and then join them with a comma
        // AND surround the artist names in links with the following format
        // https://hsmusic.wiki/artist/{artist_name_without_artist:}
        // so we'll use a regex to remove the artist: part, and then map each artist to a link
        // finally, we'll join the links with a comma
        const artistsHTML = game.song.artist.map((artist) => {
            const artistName = artist.replace('artist:', '');
            return `<a style="text-decoration: underline; color: inherit;" href="https://hsmusic.wiki/artist/${artistName}" target="_blank">${deSlugify(artistName)}</a>`;
        }).join(', ');
        return artistsHTML;
    }

    function getMinutesUntilMidnight() {
        const now = new Date();
        const utcMidnight = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
        const utcMidnightMs = utcMidnight.getTime();
        const utcMidnightPlus24hMs = utcMidnightMs + 24 * 60 * 60 * 1000;
        const timeUntilMidnightMs = utcMidnightPlus24hMs - now.getTime();
        const timeUntilMidnightMinutes = Math.floor(timeUntilMidnightMs / (60 * 1000));
        return timeUntilMidnightMinutes;
    }

    function getHumanReadableUntilMidnightString() {
        const timeUntilMidnightMinutes = getMinutesUntilMidnight();
        const timeUntilMidnightHours = Math.floor(timeUntilMidnightMinutes / 60);
        const timeUntilMidnightMinutesLeft = timeUntilMidnightMinutes - timeUntilMidnightHours * 60;
        let timeUntilMidnightString = `in ${timeUntilMidnightMinutes} minutes`;
        if (timeUntilMidnightHours > 0) {
            timeUntilMidnightString = `in ${timeUntilMidnightHours} hours, ${timeUntilMidnightMinutesLeft} minutes`;
        }
        return timeUntilMidnightString;
    }

    function getMotifsState() {
        // this is going to return square emojis with a color based on each motif's rarity, or a X emoji if it was missed
        // going displayedMotif by displayedMotif, we'll check if it was guessed or not
        // if it was guessed, we'll return the emoji for its rarity
        // if it wasn't, we'll return the X emoji
        let motifsString = '';
        game.displayedMotifs.forEach((motif) => {
            if (motif.isGuessed) {
                motifsString += rarityEmojis[motif.rarity];
            } else {
                motifsString += '❌';
            }
        });
        return motifsString;
    }

    function copyGameState(url=false, urlEmbed=false) {
        console.log(`Copying game state to clipboard with url=${url} and urlEmbed=${urlEmbed}`);
        const baseString = 'Homestuck Motifle'
        const gameState = `${baseString} ${game.dateString} (${game.points} / ${game.maxPoints})\n${getMotifsState()}`;
        if (url === true) {
            // add the url at the end
            navigator.clipboard.writeText(`${gameState}\nPlayed at <https://motifle.homestuck.net>`);
        } else if (urlEmbed === true) {
            navigator.clipboard.writeText(`${gameState}\nPlayed at https://motifle.homestuck.net`);
        } else {
            navigator.clipboard.writeText(gameState);
        }
    }

    function copyWithUrlEmbed() {
        copyGameState(false, true);
    }
    function copyWithoutUrlEmbed() {
        copyGameState(true, false);
    }
    function copyWithoutUrl() {
        copyGameState(false, false);
    }

</script>

{#if game}
    <div class="endgame-container {game.status}" in:slide={{ duration: 500 }}>
        <h2>{game.status === 'won' ? 'Congratulations! The song was:' : 'Better luck next time! The song was:'}</h2>
        <p><a href={game.song.wikiUrl} target="_blank">{game.song.name}</a> by <span class="artist-links">{@html artistsHTML}</span> ({game.song.albumName})</p>
        <p><a href={game.song.url} target="_blank">Listen on {game.song.urlType == 'youtube' ? 'Youtube' : 'Soundcloud'}</a></p>
        <h3>Total points: {game.points} / {game.maxPoints}</h3>

        {#if isCurrentGame}<p>Come back in {countdownTime} for a new game!</p>{/if}
        <div class="button-row">
            <button on:click={copyWithUrlEmbed}>Copy Results</button>
            <button on:click={copyWithoutUrlEmbed}>Copy Results (no Discord embed)</button>
            <button on:click={copyWithoutUrl}>Copy Results (no links)</button>
        </div>
    </div>
{/if}

<style>
    .endgame-container {
        border-radius: 20px 20px 0 0;
        padding: 20px;
        transition: background-color 0.5s;
    }

    .endgame-container a {
        color: inherit;
        text-decoration: underline;
    }

    /* Styles depending on game status */
    .won {
        background-color: rgb(206, 254, 206);
    }
    
    .lost {
        background-color: rgb(255, 216, 216);
    }
</style>
