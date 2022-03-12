//variabili
const checks = document.getElementsByClassName('check');
var k;
var users;
var num_players;
var N;
//chiamata ajax per avere i dati
$.ajax({
    url: url,
    type: 'GET',
    dataType: 'json',
    success: function (response) {
        k = parseInt(response.K);
        users = response.elos;
        N = Object.keys(users).length;
        users = Object.fromEntries(Object.entries(users).map(
            ([k, v]) => [k,
                {   //trasformo negli elementi html per averli sempre pronti
                    'elo': v.elo,
                    'check': document.getElementById(v.check),
                    'exp': document.getElementById(v.exp),
                    'inp': document.getElementById(v.inp),
                    'nelo': document.getElementById(v.nelo)
                }]
        ));
    },
})
//funzione per calcolare gli expected
function expected(presences) {
    let expected = Object.fromEntries(
        Object.entries(presences).map(([k,v])=>[k,
            v.presence*Object.entries(presences).map(([j,w])=>
                (j != k) * w.presence * 1 /(1+Math.pow(10, (w.elo - v.elo)/400))
            ).reduce((acc, cur)=>acc+cur,0)
        ])
    )
    return expected
}
//funzione checkbox
function checkBox () {
    //vedo quanti check ci sono
    let checked = [...checks].map(check => Number(check.checked));
    num_players = checked.reduce((acc, cur) => acc + cur, 0);
    //se sono almeno due
    if (num_players >= 2) {
        //calcolo gli expected
        let presences = Object.fromEntries(
            Object.entries(users).map(([k, v]) => [k, { 'presence': Number(v.check.checked), 'elo': v.elo }])
        )
        let expecteds = expected(presences);
        //aggiorno gli expected e abilito gli input
        Object.entries(users).forEach(function ([k, v]) {
            if (v.check.checked) {
                v.exp.textContent = String(expecteds[k].toFixed(2)).replace('.', ',');
                v.inp.disabled = false;
            } else {
                v.exp.textContent = '-';
                v.inp.value = '';
                v.inp.disabled = true;
            }           
        });
    } else {
        //scorro tutti gli utenti e rimetto allo stato iniziale
        Object.values(users).forEach(function (v) {
            v.exp.textContent = '-';
            v.inp.value = '';
            v.inp.disabled = true;
            v.nelo.textContent = Math.round(v.elo);
        });
    }
}
//funzione per gli input
var newElo = function () {
    let nelo;
    //prendo l'utente corrispondente
    let user = users[this.id];
    //controllo che ci sia corrispondenza
    if (user.inp != this) { return }
    //se vuoto
    if (this.value == '') {
        //rimetto allo stato iniziale
        nelo = Math.round(user.elo);
    } else {
        //recupero i valori
        let actual = Number(user.inp.value);
        let exp = Number(user.exp.textContent.replace(',', '.'));
        let elo = user.elo;
        //calcolo l'elo
        nelo = elo + k * (num_players / N) * (actual - exp);
    }
    //aggiorno l'elo
    user.nelo.textContent = Math.round(nelo);
}
