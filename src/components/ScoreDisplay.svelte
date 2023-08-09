<script>
    import { MAX_ERRORS } from '../models/Game.js';
    import { onMount } from 'svelte';

    export let game, displayedMotifs;

    let mounted = false;
    onMount(() => {
        mounted = true;
    });    
    let points = 0;
    let maxPoints = 0;
    let nLeitmotifsGuessed = 0;
    let nTotalLeitmotifs = 0;
    let errorCount = 0;
    let shakeKey = 0;
    $: if (game || displayedMotifs) {
        if(mounted && (game.errorCount > errorCount)) {
            shakeKey++;
        }
        points = game.points;
        maxPoints = game.maxPoints;
        nLeitmotifsGuessed = game.nLeitmotifsGuessed;
        nTotalLeitmotifs = game.nTotalLeitmotifs;
        errorCount = game.errorCount;
    }
</script>

<style>
.score-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    padding: 5px 15px;
    flex: 1;
    max-width: 148px;
    background-color: white;
    color: var(--color-text);
}

.score-text, .error-text {
    font-size: 16px;
    margin-bottom: 5px;
}

.leitmotif-count {
    font-size: 14px;
    margin-bottom: 5px;
}

.progress-bar {
    width: 100%;
    height: 10px;
    background-color: #eee;
    border-radius: 5px;
    overflow: hidden;
    position: relative;
}

.progress-bar-fill {
    transition: width 0.5s ease-out;
    height: 10px;
    background-color: var(--progress-color, var(--color-theme-1));
    width: calc(100% * (var(--guessed) / var(--total)));
    border-radius: 5px;
}

.error-circle-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 4px;
    margin-bottom: 5px;
}

.error-circle {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #eee;
}

.error-circle.filled {
    background-color: red;
}

.shake {
    animation: shake 0.4s;
}
</style>

{#key shakeKey}
<div class={shakeKey > 0 ? 'score-container shake' : 'score-container'}>
    <div class="error-text">
        <div class="error-circle-container">
            {#each Array(MAX_ERRORS) as _, i}
                <div class="error-circle {i < errorCount ? 'filled' : ''}"></div>
            {/each}
        </div>
    </div>
    <div class="score-text">{points}/{maxPoints} pts.</div>
    <div class="progress-bar">
        <div class="progress-bar-fill" style="--guessed: {nLeitmotifsGuessed}; --total: {nTotalLeitmotifs}; --progress-color: {nLeitmotifsGuessed === nTotalLeitmotifs ? 'green' : ''}"></div>
    </div>
</div>
{/key}
