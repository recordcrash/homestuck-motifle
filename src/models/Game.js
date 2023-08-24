export const GAME_STATUS = {
    ONGOING: 'ongoing',
    WON: 'won',
    LOST: 'lost'
};

// based off number of songs in each rarity group, we'll assign a point value to each rarity
// motifs included in more songs are worth less points, 5 being the most commonly referenced
export const RARITY_POINTS = {
    1: 500,
    2: 250,
    3: 175,
    4: 125,
    5: 100
};

class Game {
    constructor(dateString, songsArray, motifsArray) {
        this.dateString = dateString;
        this.song = songsArray.find((song) => song.day === dateString);
        this.submittedMotifs = [];
        this.displayedMotifs = this.initializeDisplayedMotifs(motifsArray);
        this.status = GAME_STATUS.ONGOING;
        this.errorCount = 0;
        this.maxPoints = this.initializeMaxPoints();
        this.maxErrors = this.initializeMaxErrors();
    }

    
    get submittedMotifSlugs() {
        return this.submittedMotifs.map((motif) => motif.slug);
    }

    get isGuessed() {
        // all target leitmotifs in song.leitmotifs (in the form track:trackslug, track:trackslug2, etc.) are included in submittedMotifs (or their .slug properties)
        return this.song.leitmotifs.every((leitmotifSlug) => this.submittedMotifSlugs.includes(leitmotifSlug));
    }

    get isGameActive() {
        return this.status === GAME_STATUS.ONGOING;
    }

    get points() {
        // points is the sum of the points of all the motifs that have been guessed
        const pointsSum = this.displayedMotifs.reduce((acc, motif) => {
            if (motif.isGuessed) return acc + motif.points;
            return acc;
        }, 0);
        // and then minus errors * 1 pts, min 0
        const points = Math.max(pointsSum - (this.errorCount * 1), 0);
        return points;
    }

    get nLeitmotifsGuessed() {
        return this.displayedMotifs.reduce((acc, motif) => {
            if (motif.isGuessed) return acc + 1;
            return acc;
        }, 0);
    }
    
    get nTotalLeitmotifs() {
        return this.displayedMotifs.length;
    }

    hydrateWithObject(gameObject) {
        // grabs all data from a localStorage stored game object and sets it to the current game object
        this.dateString = gameObject.dateString;
        this.song = gameObject.song;
        this.submittedMotifs = gameObject.submittedMotifs;
        this.displayedMotifs = gameObject.displayedMotifs;
        this.status = gameObject.status;
        this.errorCount = gameObject.errorCount;
        this.maxPoints = gameObject.maxPoints || this.initializeMaxPoints();
        this.maxErrors = gameObject.maxErrors || this.initializeMaxErrors();
    }

    initializeMaxPoints() {
        // based on rarity, a song is worth a certain number of points. we'll initialize the maxPoints to that number
        // to show to the user, and then we'll subtract points as they make mistakes
        const points = this.displayedMotifs.reduce((acc, motif) => {
            return acc + (RARITY_POINTS[motif.rarity] || 0);
        }, 0);
        return points;
    }

    initializeMaxErrors() {
        // the max number of errors is the number of motifs in the song, minus one, or 3, whichever is higher, and 10, whichever is lower
        // so if there's 5 motifs, the max errors is 4, if there's 2 motifs, the max errors is 3, if there's 20 motifs, the max errors is 10
        return Math.min(Math.max(this.displayedMotifs.length - 1, 3), 10);
    }

    checkBallpark(motif) {
        // some songs are in the ballpark of the target song, but not quite right
        // we have lists of songs that sound almost exactly the same. in that case we'll tell the user and not count it as an error
        // we'll have lists of lists of slugs and compare them. if we can find both slugs in the same list, we'll return true
        // thanks to quasarNebula for 70% of the list!
        const ballparkList = [
            ['doctor', 'doctor-original-loop'],
            ['flare', 'flare-cascade'],
            ['cascade', 'cascade-beta'],
            ['showtime-original-mix', 'showtime-piano-refrain', 'showtime-imp-strife-mix'],
            ['three-in-the-morning', '3-in-the-morning-pianokind', 'three-in-the-morning-rj'],
            ['liquid-negrocity', 'black'],
            ['sunsetter', 'sunslammer'],
            ['MeGaLoVania', 'megalovania-halloween', 'megalovania-undertale'],
            ['dissension-original', 'dissension-remix'],
            ['black-hole-green-sun', 'black-rose-green-sun'],
            ['sburban-jungle', 'sburban-jungle-brief-mix', 'sburban-countdown'],
            ['harlequin', 'harleboss', 'hardlyquin'],
            ['verdancy-bassline', 'kinetic-verdancy'],
            ['beatdown-strider-style', 'strider-showdown-loop'],
            ['chorale-for-jaspers', 'hardchorale'],
            ['the-ballad-of-jack-noir-original', 'the-ballad-of-jack-noir'],
            ['hauntjelly', 'hauntjam'],
            ['carefree-victory', 'carefree-action'],
            ['atomyk-ebonpyre', 'tribal-ebonpyre'],
            ['guardian', 'guardian-v2'],
            ['endless-climb', 'clockwork-melody'],
            ['homestuck', 'elevatorstuck', 'homestuck-anthem'],
            ['skaian-skirmish', 'skaian-skuffle'],
            ['savior-of-the-waking-world', 'savior-of-the-dreaming-dead', 'penumbra-phantasm'],
            ['courser', 'umbral-ultimatum', 'an-unbreakable-union'],
            ['skaian-flight', 'skaian-overdrive', 'skaian-ride', 'skaian-happy-flight'],
            ['pumpkin-cravings', 'this-pumpkin'],
            ['crystamanthequins', 'crystalanthemums', 'crystalanthology'],
            ['lotus-bloom', 'lotus', 'lotus-land-story'],
            ['how-do-i-live', 'how-do-i-live-bunny-back-in-the-box-version'],
            ['ruins', 'ruins-with-strings'],
            ['the-beginning-of-something-really-excellent', 'gardener'],
            ['candles-and-clockwork-alpha-version', 'candles-and-clockwork'],
            ['karkats-theme', 'crustacean'],
            ['arisen-anew', 'psych0ruins'],
            ['nepetas-theme', 'walls-covered-in-blood'],
            ['virgin-orb', 'darling-kanaya'],
            ['the-la2t-frontiier', 'the-blind-prophet'],
            ['vriskas-theme', 'spiders-claw'],
            ['alternia', 'theme'],
            ['ocean-stars', 'ocean-stars-falling'],
            ['clockwork-apocalypse', 'clockwork-reversal'],
            ['eternity-served-cold', 'english'],
            ['i-dont-want-to-miss-a-thing-aerosmith', 'i-dont-want-to-miss-a-thing'],
            ['wsw-beatdown', 'walk-stab-walk-rande'],
            ['horschestra-STRONG-version', 'horschestra'],
            ['trollcops', 'under-the-hat'],
            ['serenade', 'requited'],
            ['hate-you', 'love-you-feferis-theme'],
            ['im-a-member-of-the-midnight-crew-acapella', 'im-a-member-of-the-midnight-crew'],
            ['stress', 'five-four-stress']
        ]
        let notAlreadyGuessedSlugs = this.displayedMotifs.filter((displayedMotif) => !displayedMotif.isGuessed).map((displayedMotif) => displayedMotif.slug);
        notAlreadyGuessedSlugs = notAlreadyGuessedSlugs.map((slug) => slug.replace('track:', ''));
        const motifSlug = motif.slug.replace('track:', '');
        const found = ballparkList.some((list) => {
            return list.includes(motifSlug) && list.some((slug) => notAlreadyGuessedSlugs.includes(slug));
        });
        return found;
    }

    submitMotif(motif) {
        // Logic to handle motif submission.
        let success = 'error';

        // Before anything, check the user didn't submit the motif of the current song, instead of its child motifs
        if (motif.slug === `track:${this.song.slug}`) return 'same';

        this.submittedMotifs.push(motif);
        const submittedMotif = this.submittedMotifs.find((submittedMotif) => submittedMotif.slug === motif.slug);
        
        const displayedMotifToUpdate = this.displayedMotifs.find((displayedMotif) => displayedMotif.slug === motif.slug);
        if (displayedMotifToUpdate) {
            displayedMotifToUpdate.isGuessed = true;
            submittedMotif.isGuessed = true;
            success = 'success';
        } else {
            if (!this.checkBallpark(motif)) this.errorCount++;
            else success = 'partial';
        }
        
        // Check game end condition.
        this.checkGameEnd();
        return success;
    }

    checkGameEnd() {
        // Logic to determine if the game is won or lost.
        if (this.errorCount >= this.maxErrors) {
            this.endGame(GAME_STATUS.LOST);
        } else if (this.isGuessed) {
            this.endGame(GAME_STATUS.WON);
        }
    }

    endGame(result) {
        // Logic to handle game ending.
        this.status = result;
    }

    initializeDisplayedMotifs(motifsArray) {
        // first let's turn the motif slugs stored in song.leitmotifs into the actual motif objects
        let motifObjects = this.song.leitmotifs.map((leitmotifSlug) => motifsArray.find((motif) => motif.slug === leitmotifSlug));
        // sort by rarity, highest first
        motifObjects.sort((a, b) => b.rarity - a.rarity);
        // filter out undefined motifObjects
        motifObjects = motifObjects.filter((motif) => motif);
        // now let's create a new array of motif objects with the same properties as the motif objects we just created, but with a new property, "isGuessed", which is set to false
        return motifObjects.map((motif) => {
            return {
                ...motif,
                points: RARITY_POINTS[motif.rarity],
                isGuessed: false
            };
        });
    }
}

export default Game;