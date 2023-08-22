<svelte:head>
    <title>How to play Motifle</title>
    <meta name="description" content="How to play Motifle" />
</svelte:head>

<div class="text-column">
    <h1>How to play Motifle</h1>

    <p>
        In this musical game, your main goal is to <b>guess a song's referenced melodies</b>. For instance, the song <a class="rarity4" href="https://hsmusic.wiki/track/descend">Descend</a> prominently features the drums from <a class="rarity5" href="https://hsmusic.wiki/track/upward-movement-dave-owns">Upward Movement</a>, that sequence where Dave rose to the highest point of his building. Listen carefully to the song and use the search bar to identify motifs!
    </p>

    <p>
        Points are awarded based on the rarity of the guessed motif:
        <ul>
            <li><span class="bold rarity5">Core (100 points)</span>: Official melodies that every Homestuck fan has heard multiple times, like <a class="rarity5" href="https://hsmusic.wiki/track/sburban-jungle">Sburban Jungle</a> from [S] Enter and others.</li>
			<li><span class="bold rarity4">Common (125 points)</span>: Either popular fanmusic melodies like <a class="rarity4" href="https://hsmusic.wiki/track/moshi-moshi">Moshi Moshi</a> or slightly less common official melodies like <a class="rarity4" href="https://hsmusic.wiki/track/crystamanthequins">Crystamanthequins</a>, which you might remember from [S] Make Her Pay.</li>
			<li><span class="bold rarity3">Uncommon (175 points)</span>: Melodies that are not as popular as the previous two categories, like <a class="rarity3" href="https://hsmusic.wiki/track/an-unbreakable-union">An Unbreakable Union</a> or <a class="rarity3" href="https://hsmusic.wiki/track/arisen-anew">Arisen Anew</a>.</li>
			<li><span class="bold rarity2">Rare (250 points)</span>: At this point you might not even know the songs, like <a class="rarity2" href="https://hsmusic.wiki/track/blue-atom">Blue Atom</a> or <a class="rarity2" href="https://hsmusic.wiki/track/contact">CONTACT</a>.</li>
			<li><span class="bold rarity1">Singular (500 points)</span>: Near impossible melodies to guess—they have only appeared once in our dataset. For example, <a class="rarity1" href="https://hsmusic.wiki/track/a-fashionable-escape">A Fashionable Escape</a> or <a class="rarity1" href="https://hsmusic.wiki/track/gasters-theme">Gaster's Theme</a>.</li>
        </ul>

    <p>
        You have a limited number of guesses, that scale from 3 to 10 based on the number of motifs in the song. Keep an eye on the unfilled circles above the score. The game concludes once you've used all your guesses, identified all motifs, or clicked on the "GIVE UP" option.
    </p>

    <p>
        Once the game ends, songs are revealed along with links to the <a href="https://hsmusic.wiki">Homestuck Music Wiki</a>. Share your scores on your favorite social networks, by clicking on the share buttons! We recommend sharing in the <a href="https://discord.gg/homestuck">Homestuck Discord</a>'s Heardle/Motifle thread, which is frequented by around 20 people every day.
    </p>
</div>

<script>
    
</script>

<style>
.text-column {
    background-color: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* Optional: adds a subtle shadow to give the container some depth */
    max-width: 800px; /* Optional: to limit the width if displayed on very wide screens */
    margin: 2rem auto; /* Centers the container horizontally */
}
a {
	text-decoration: underline;
}

.bold {
	font-weight: bold;
}

li {
    margin-bottom: 0.5rem;
    line-height: 1.4;
}
</style>
