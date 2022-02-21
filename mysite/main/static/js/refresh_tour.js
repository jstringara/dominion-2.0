setInterval(function () {
    //uso ajax per fare la richiesta
    $.ajax({
        url: refresh_url,
        type: "GET",
        success: function(response){
            //se ho un warning chiudo tutto
            if (response.warning) {
                main.innerHTML = response.warning;
            }
            //se no procedo normalmente
            else {
                //confronto la data e aggiorno
                if (date.placeholder!=response.date){
                    refreshInput(date, response.date);
                }
                //confronto con i dati e aggiorno
                let are_equal = arrayEqual(placeholders(),response.array);
                if (!are_equal) {
                    //aggiorno la tabella
                    refreshTable(response.array, response.awards);
                    //aggiorno i totali
                    refreshTotals(response.totals);
                }
            }
        }
    });
}, 5000);
