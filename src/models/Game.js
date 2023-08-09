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

export const MAX_ERRORS = 3;

class Game {
    constructor(dateString, songsArray, motifsArray) {
        this.dateString = dateString;
        this.song = songsArray.find((song) => song.day === dateString);
        this.submittedMotifs = [];
        this.displayedMotifs = this.initializeDisplayedMotifs(motifsArray);
        this.status = GAME_STATUS.ONGOING;
        this.errorCount = 0;
        this.maxPoints = this.initializePoints();
    }

    hydrateWithObject(gameObject) {
        // grabs all data from a localStorage stored game object and sets it to the current game object
        this.dateString = gameObject.dateString;
        this.song = gameObject.song;
        this.submittedMotifs = gameObject.submittedMotifs;
        this.displayedMotifs = gameObject.displayedMotifs;
        this.status = gameObject.status;
        this.errorCount = gameObject.errorCount;
    }

    initializePoints() {
        // based on rarity, a song is worth a certain number of points. we'll initialize the maxPoints to that number
        // to show to the user, and then we'll subtract points as they make mistakes
        const points = this.displayedMotifs.reduce((acc, motif) => {
            return acc + (RARITY_POINTS[motif.rarity] || 0);
        }, 0);
        return points;
    }

    checkBallpark(motif) {
        // some songs are in the ballpark of the target song, but not quite right
        // we have lists of songs that sound almost exactly the same. in that case we'll tell the user and not count it as an error
        // we'll have lists of lists of slugs and compare them. if we can find both slugs in the same list, we'll return true
        const ballparkList = [
            ['doctor', 'doctor-original-loop'],
            ['flare', 'flare-cascade'],
            ['cascade', 'cascade-beta'],
            ['homestuck', 'homestuck-anthem'],
            ['showtime-original-mix', 'showtime-piano-refrain', 'showtime-imp-strife-mix'],
            ['savior-of-the-waking-world', 'penumbra-phantasm'],
            ['three-in-the-morning', 'three-in-the-morning-rj', '3-in-the-morning-pianokind'],
            ['liquid-negrocity', 'black'],
            ['sunsetter', 'sunslammer'],
            ['MeGaLoVania', 'megalovania-halloween', 'megalovania-undertale'],
            ['dissension-original', 'dissension-remix'],
            ['black-rose-green-sun', 'black-hole-green-sun']
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

        if (this.errorCount >= MAX_ERRORS) {
            this.endGame(GAME_STATUS.LOST);
        } else if (this.isGuessed) {
            this.endGame(GAME_STATUS.WON);
        }
    }

    endGame(result) {
        // Logic to handle game ending.
        this.status = result;
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
        // and then divided depending on number of errors, 1 error = 75% of points, 2 errors = 50% of points, 3 errors = 25% of points
        const errorMultiplier = 1 - (this.errorCount * 0.25);
        return Math.floor(pointsSum * errorMultiplier);
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

    initializeDisplayedMotifs(motifsArray) {
        // first let's turn the motif slugs stored in song.leitmotifs into the actual motif objects
        const motifObjects = this.song.leitmotifs.map((leitmotifSlug) => motifsArray.find((motif) => motif.slug === leitmotifSlug));
        // sort by rarity, highest first
        motifObjects.sort((a, b) => b.rarity - a.rarity);
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