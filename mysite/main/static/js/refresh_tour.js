setInterval(function(){
    //estraggo i vecchi value della tabella tramite i placeholder
    let rows = document.getElementById("tour_table").rows;
    var data = []
    let tLength = rows.length;
    for (let i=0; i<tLength; i++) {
        var row = [...rows[i].getElementsByTagName('input')].map(u=>u.placeholder);
        data.push(row);
    };
    //estraggo la data
    var date = document.getElementById("date");
    //funzione di confronto
    function arrayEqual(ar1,ar2) {
        return JSON.stringify(ar1)==JSON.stringify(ar2);
    };
    //uso ajax per fare le varie richieste
    $.ajax({
        //prima richiesta
        url: refresh_url,
        type: "GET",
        success: function(response){
            //se ho un warning chiudo tutto
            if (response.warning) {
                let warn = document.getElementById('warning');
                warn.innerHTML = response.warning;
            };
            //confronto la data
            if (date.placeholder!=response.date){
                date.value = response.date;
                date.placeholder = response.date;
            }
            //confronto con i dati
            var are_equal = arrayEqual(data,response.array);
            if (!are_equal) {
                //scorro il tbody input per input e cambio i value ed i placeholder
                var inputs = [];
                for (row of rows){
                    inputs.push(row.getElementsByTagName("input"));
                };
                for (let i=0; i<inputs.length; i++){
                    for (let j=0; j<inputs[i].length; j++){
                        //aggiorno il valore ed il placeholder
                        inputs[i][j].value = response.array[i][j];
                        inputs[i][j].placeholder = response.array[i][j];
                    }
                };
                //scorro il tbody dei totali e faccio come prima
                rows = document.getElementById('total_table').rows;
                var cells = [];
                for (row of rows){
                    cells.push(row.getElementsByClassName("cell"));
                };
                for (let i=0; i<cells.length; i++){
                    for (let j=0; j<cells[i].length; j++){
                        cells[i][j].textContent = response.totals[i][j];                        }
                };
            }
            else {
                console.log('stessi');
            }
        }
    });
}, 5000);
