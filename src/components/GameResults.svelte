<script>
    import { slide } from 'svelte/transition';
    import { onMount } from 'svelte';

    export let game;

    let countdownTime;
    
    onMount(() => {
        const now = new Date();
        const midnight = new Date(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1, 0, 0, 0);
        countdownTime = Math.floor((midnight - now) / 1000 / 60); // in minutes
    });

    function copyGameState(url=false, urlEmbed=false) {
        console.log(`Copying game state to clipboard with url=${url} and urlEmbed=${urlEmbed}`);
        const baseString = 'Homestuck Motifle'
        const gameState = `${baseString} ${game.dateString}\n🎵 ${game.points} / ${game.maxPoints} points 🎵`;
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
        <p><a href={game.song.wikiUrl} target="_blank">{game.song.name}</a> ({game.song.albumName})</p>
        <p><a href={game.song.url} target="_blank">Listen on {game.song.urlType == 'youtube' ? 'Youtube' : 'Soundcloud'}</a></p>
        <h3>Total points: {game.points} / {game.maxPoints}</h3>

        <p>Come back in {countdownTime} minutes for a new game!</p>
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
