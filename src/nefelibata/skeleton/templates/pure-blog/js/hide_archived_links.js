function hideArchivedLinks() {
    const archivedLinks = document.getElementsByClassName('archive');

    for (let i = 0; i < archivedLinks.length; i++) {
        archivedLinks[i].style.display = 'none';
    }
}

window.addEventListener('load', hideArchivedLinks);
