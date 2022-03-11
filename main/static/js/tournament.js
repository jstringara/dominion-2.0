//variabili globali

/*prendo gli elementi HTML come costanti
per non riprenderli ogni volta*/
const table = document.getElementById("tour_table");
const date = document.getElementById("date");
const content = document.getElementById("content")
const warning = document.getElementById("warning");
const success = document.getElementById("success")
const is_valid = $("#tour_form").valid();
const inputs = [...table.rows].map(
    u => u.getElementsByTagName("input")
);
const names = [...table.rows].map(
    u => u.getElementsByTagName("td")[0]
);
const totals = [...document.getElementById('total_table').rows].map(
    u => u.getElementsByClassName("cell")
);

//funzioni globali

//funzione di confronto
function arrayEqual(ar1,ar2) {
    return JSON.stringify(ar1)==JSON.stringify(ar2);
}
//funzione che aggiorna placeholder e value di un input
function refreshInput(input, val) {
    if (input.value == input.placeholder) {    
        input.value = val;
    }
    input.placeholder = val;
}
//funzione che aggiorna la casella del nome
function refreshName(cell, new_name, is_award) {
    //cambio il nome
    let name = cell.getElementsByClassName("name")[0];
    name.innerText = new_name;
    //tolgo la coccarda
    let award = cell.getElementsByClassName("bi bi-award")[0];
    if (award) { award.remove(); }
    //se premiato la aggiungo
    if (is_award) {
        let award = document.createElement("i");
        award.classList.add("bi", "bi-award");
        cell.appendChild(award);
    }
}
//funzione che aggiorna una cella dei totali
function refreshTotal(cell, text) {
    text = String(text).replace('.', ',');
    cell.textContent = text;
}
//funzione che modifica la visibilità di un elemento
function toggleDisplayStatus(x) {
    if (x.style.display === "none") {
        x.style.display = "block";
    }
    else {
        x.style.display = "none";
    }
}
//funzione che verifica se un elemento è nascosto
function isHidden(x) {
    return Boolean(x.style.display == "none");
}
//funzione che attiva e disattiva il warning
function toggleWarning(message) {
    //se nascosto e ho un messaggio attivo
    if (isHidden(warning)&&message){
        let msg = document.getElementById('warning_message');
        msg.innerText = message;
        toggleDisplayStatus(warning);
        toggleDisplayStatus(content);
    }
    //se attivo ma nessun messaggio
    else if (!isHidden(warning) && !message) {
        //refresho
        window.location.href = window.location.href;
    }
}
//funzione che attiva il success
function toggleSuccess(message) {
    let msg = document.getElementById('success_message');
    msg.textContent = message;
    if (isHidden(success)) {
        toggleDisplayStatus(success);
    }
}
//funzione per estrarre i placeholder dalla tabella
var placeholders = function () {
    return inputs.map(u => [...u].map(u => u.placeholder));
};
//funzione che estrae i valori dalla tabella
var values = function () {
    return inputs.map(u => [...u].map(u => u.value));
};
//funzione che aggiorna gli inputs e le coccarde dati due array
var refreshTable = function (array, awards) {
    //scorro gli input e aggiorno
    inputs.forEach(
        (u, i) => [...u].forEach(
            (w, j) => refreshInput(w, array[i][j])
        )
    );
    //scorro i nomi e li aggiungo
    names.forEach(
        (u, i) => refreshName(u, awards[i][0], awards[i][1])
    );
};
//funzione che aggiorna la tabella dei totali
var refreshTotals = function (array) {
    totals.forEach(
        (u, i) => [...u].forEach(
            (w, j) => refreshTotal(w,array[i][j]) 
        )
    );
};
