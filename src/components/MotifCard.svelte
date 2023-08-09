<script>
    export let motif;
    export let forceReveal = false;
    export let currentGame;
    
    let isLoading = true;
    let hasError = false;
    let actualImageSrc;
    
    const unknownImage = '/unknown.gif';
    const errorImage = '/error.gif';
    
    function loadImage() {
        const img = new Image();

        img.onload = () => {
            isLoading = false;
            actualImageSrc = motif.imageUrl;
        };

        img.onerror = () => {
            isLoading = false;
            actualImageSrc = errorImage;
            hasError = true;
        };

        img.src = motif.imageUrl;
    }

    $: if (motif.isGuessed || forceReveal) {
        loadImage();
    } else {
        actualImageSrc = unknownImage;
        isLoading = false;
    }

    $: displayName = currentGame && currentGame.errorCount >= 2 
        ? `Unknown (${motif.albumName})` 
        : 'Unknown';
    
    let rarityClass = `raritybg${motif.rarity} rarity${motif.rarity}`;
</script>

{#if !isLoading}
<div class={`card ${rarityClass} ${motif.isGuessed ? 'isGuessed' : ''} ${forceReveal ? 'forceReveal' : ''}`}>
    <div class="card-inner">
        <div class="front">
            <img src={unknownImage} class="card-image" />
            <div class="card-content">
                <h3>{displayName}</h3>
            </div>
        </div>
        <div class="back">
            {#if hasError}
                <img src={errorImage} class="card-image" />
                <div class="card-content">
                    <h3>{motif.name}</h3>
                </div>
            {:else}
                <img src={actualImageSrc} class="card-image" />
                <div class="card-content">
                    <h3>{motif.name}</h3>
                </div>
            {/if}
        </div>
    </div>
</div>
{/if}

<style>
    .card {
        perspective: 1000px;
        display: flex;
        align-items: center;
        padding: 0 10px;
        border-radius: 5px;
        margin: 10px 0;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        white-space: normal;
        height: 80px;
        width: auto;
        position: relative;  /* Make .card a positioning context */
    }

    .card-inner {
        width: 100%;
        height: 100%;
        transform-style: preserve-3d; 
        transition: transform 0.5s, opacity 0.5s;  /* Adjusted to add opacity transition */
        position: relative; 
    }

    .front, .back {
        position: absolute;
        backface-visibility: hidden; 
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        display: flex;
        align-items: center;
    }

    .front {
        transform: rotateX(0deg);
    }

    .back {
        transform: rotateX(-180deg);
    }

    .card.isGuessed .card-inner, .card.forceReveal .card-inner {
        transform: rotateX(180deg);
    }

    /* Hide the .front at the half-way point during the flip */
    .card.isGuessed .front, .card.forceReveal .front {
        opacity: 0;
    }


    .card.forceReveal {
        background-color: rgb(255, 107, 107) !important;
    }

    .card-image {
        width: 60px;
        height: 60px;
        margin-right: 10px;
        object-fit: cover;
    }
    
    .card-content {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .card-content h3 {
        margin: 0;
        font-size: 14px;
    }
</style>
