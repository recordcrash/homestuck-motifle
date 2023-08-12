<script>
import { onMount } from 'svelte';
import Game, { GAME_STATUS } from '../models/Game';
import MotifCard from '../components/MotifCard.svelte';
import GameResults from '../components/GameResults.svelte';
import ScoreDisplay from '../components/ScoreDisplay.svelte';
import MediaPlayer from '../components/MediaPlayer.svelte';
import Typeahead from "svelte-typeahead";
import { slide, fade, fly } from 'svelte/transition'
import { tick } from 'svelte';

let showToast = false;
let toastMessage = '';

let forceReveal = false;

let gameDataLoaded = false;
let games = {}; // This will store all the games loaded from localStorage.
let currentGame; // This will hold the game of the current day.

let gameMotifs = [];
let gameSongs = [];
const extractMotif = (motif) => motif.name;

let selectedDate = new Date();
let selectedDateString = selectedDate.toISOString().slice(0, 10);
const firstDayString = '2023-08-09';
const lastDayString = new Date().toISOString().slice(0, 10);

let selectedMotif;
let displayedMotifs;

function saveGamesToLocalStorage() {
    localStorage.setItem('games', JSON.stringify(games));
}

function loadGamesFromLocalStorage() {
    const savedGames = localStorage.getItem('games');
    if (savedGames) {
        const jsonGames = JSON.parse(savedGames);
		const games = {};
		for (const dateString in jsonGames) {
			const game = jsonGames[dateString];
			games[dateString] = new Game(dateString, gameSongs, gameMotifs);
			try {
				games[dateString].hydrateWithObject(game);
			} catch (e) {
				console.error(`Error hydrating game for date ${dateString}: ${e}, erasing game.`);
				delete games[dateString];
			}
		}
		return games;
    }
    return {};
}

// Reactive statement to load the game for the selected date.
$: if (gameDataLoaded) {
    loadGameForSelectedDate(selectedDateString);
}

function loadGameForSelectedDate(dateString) {
	console.log(`Loading game for date ${dateString}`)
	if (!games[dateString]) {
		currentGame = new Game(dateString, gameSongs, gameMotifs);
		games[dateString] = currentGame;
		saveGamesToLocalStorage();
	} else {
		currentGame = games[dateString];
	}
	console.log(currentGame);
	displayedMotifs = [...currentGame.displayedMotifs];
	if (currentGame.status === GAME_STATUS.LOST) {
		forceReveal = true;
	} else {
		forceReveal = false;
	}
}

async function loadGameData() {
	const gameMotifsResponse = await fetch('/game_motifs.json');
    gameMotifs = await gameMotifsResponse.json();
    const gameSongsResponse = await fetch('/game_songs.json');
    gameSongs = await gameSongsResponse.json();

    games = loadGamesFromLocalStorage();

	gameDataLoaded = true;
}

function computeClass(result) {
	const leitmotif = result.original;
	return `motifTitle rarity${leitmotif.rarity}`;
}

function updateGame() {
	games = { ...games, [currentGame.dateString]: currentGame };
	displayedMotifs = [...currentGame.displayedMotifs];
	saveGamesToLocalStorage();
	if (currentGame.status === GAME_STATUS.LOST) {
		forceReveal = true;
	} else {
		forceReveal = false;
	}
}

function showToastMessage(message) {
    showToast = true;
    toastMessage = message;
    // Hide the toast after 3 seconds
    setTimeout(() => {
        showToast = false;
    }, 3000);
}

function handleMotif(motif, success) {
    console.log(`Submitted motif ${motif.name} with success ${success}`);

    if (success === 'success') {
        // You can add a brief celebration animation here, like a sparkle or stars.
    } else if (success === 'same') {
        showToastMessage(`Yes, the song is "${motif.name}", but you're meant to guess *its motifs*, numbnuts!`);
    } else if (success === 'partial') {
        showToastMessage(`Your guess "${motif.name}" was close! It hasn't been counted as an error.`);
    } else if (success === 'error') {
        showToastMessage(`Your guess "${motif.name}" was wrong!`);
    }
}


function submitMotif(event) {
    const motif = event.detail.original;
    const success = currentGame.submitMotif(motif);

	handleMotif(motif, success);

    updateGame();
}

function giveUp() {
	currentGame.endGame(GAME_STATUS.LOST);
	updateGame();
}

onMount(async () => {
	await loadGameData();
});
</script>

<svelte:head>
	<title>Homestuck Motifle - HOMESTUCK.NET</title>
	<meta name="description" content="Homestuck Motifle: guess the song's leitmotifs!">
</svelte:head>

<style>
.container {
	display: flex;
	flex-direction: column;
	flex: 1;
}

.cards-container {
	flex: 1;
	overflow-y: auto;
	margin: 10px 0;
	/* Other elements take more than n pixels currently, can't go beyond 100vh - n */
	max-height: calc(100vh - 250px);
}

.search-bar {
	flex-shrink: 0;
	flex-direction: row;
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin: 10px 0;
}

.first-row {
    display: flex;
    align-items: center; /* Vertically aligns items in the center */
    justify-content: space-between; /* Places maximum space between items */
    padding: 10px 0;
}


.dateInput {
	display: block;
	appearance: none;
	-webkit-appearance: none;
	-moz-appearance: none;
	-ms-appearance: none;
	border: none;
	outline: none;
	box-shadow: none;
	border-radius: 4px;
	padding: 8px 12px;
	font-size: 16px;
	color: var(--color-text);
}

:global([data-svelte-typeahead]) {
	/** align to left of parent div and only occupy 80% of the space, the other 20% will be occupied by a button **/
	flex: 1;
}

:global(.svelte-typeahead-list) {
	top: unset !important;
	position: absolute !important;
	bottom: 100% !important; /* This makes the dropdown appear above the input */
	left: 0 !important;
	width: 100% !important;
	margin: 0 !important;
	padding: 0 !important;
	list-style: none !important;
	background-color: inherit !important;
	box-shadow: 0 -4px 8px rgba(0, 0, 0, 0.1) !important; /* Notice the negative value for shadow to appear on the top */
	z-index: 1 !important; /* Optional: adjust as needed to ensure it layers above other elements */
	max-height: 200px !important;
	overflow-y: auto !important;
}

:global(.motifResult) {
	display: flex;
	flex-direction: column;
}
:global(.motifTitle) {
	font-weight: bold;
}
:global(.motifSlug) {
	font-size: 0.8em;
	color: #666;
}

/* Rarity colors, they are dark and go from rarest 1 to most common 5 */
:global(.rarity5) {
	color: rgb(74, 35, 35);
}
:global(.rarity4) {
	color: #c8a000;
}
:global(.rarity3) {
	color: #1e8200;
}
:global(.rarity2) {
	color: #0027c3;
}
:global(.rarity1) {
	color: #7a00d1;
}
:global(.rarity6) { /* This is for the error case */
	color: lightgrey;
}

:global(.raritybg5) {
	background-color: rgba(165, 42, 42, 0.1);
}
:global(.raritybg4) {
	background-color: rgba(200, 173, 0, 0.1);
}
:global(.raritybg3) {
	background-color: rgba(30, 130, 0, 0.1);
}
:global(.raritybg2) {
	background-color: rgba(0, 39, 195, 0.1);
}
:global(.raritybg1) {
	background-color: rgba(122, 0, 209, 0.1);
}

.give-up-btn {
    margin-left: 15px; 
    padding: 8px 15px;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;

    /* Optional: Basic hover effect */
    &:hover {
        background-color: #d32f2f; /* dark red */
    }
}

.toast-message {
    position: fixed;
    bottom: -60px; 
    left: 50%;
    transform: translateX(-50%);
    background-color: #333;
    color: #fff;
    padding: 15px 25px;
    border-radius: 4px;
    z-index: 10;
    transition: bottom 0.3s;
}
.show {
    bottom: 20px; 
}
</style>
{#if displayedMotifs}
<div class="container" transition:fade={{ duration: 1000 }}>
	<div class="first-row">
		<input class="dateInput" type="date" bind:value={selectedDateString} 
			min={firstDayString} max={lastDayString}/>
		<MediaPlayer game={currentGame} />
		<ScoreDisplay game={currentGame} displayedMotifs={displayedMotifs} />
	</div>

		<div class="cards-container">
			{#each displayedMotifs as motif (motif.slug)}
				<MotifCard {motif} {forceReveal} {currentGame}/>
			{/each}
		</div>


		{#if currentGame.isGameActive}
		<div class="search-bar">	
				<Typeahead hideLabel focusAfterSelect
					data={gameMotifs} extract={extractMotif} 
					bind:selected={selectedMotif} on let:result
					inputAfterSelect="clear"
					on:select={submitMotif}>
					<div class="motifResult">
						<div class={computeClass(result)}>
							{@html result.string} 
						</div>
						<div class="motifSlug">
							{result.original.slug ? result.original.slug.slice(6) : null}
						</div>
					</div>
				</Typeahead>
				<button on:click={giveUp} class="give-up-btn">GIVE UP</button>
		</div>
		{#if showToast}
			<div class="toast-message show" on:click={() => showToast = false} on:keydown={e => e.key === 'Escape' && (showToast = false)} role="presentation">
				{toastMessage}
			</div>
		{/if}
		{:else if currentGame.status === GAME_STATUS.WON || currentGame.status === GAME_STATUS.LOST}
            <GameResults game={currentGame} />
        {/if}
</div>
{/if}