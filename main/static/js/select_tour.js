//
const select = document.getElementById("select_tournament");
const tour = document.getElementById("tour");
function selectTournament() {
    let url = select.value;
    tour.href = url;
}
