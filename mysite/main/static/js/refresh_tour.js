setInterval(function () {
    //uso ajax per fare la richiesta
    $.ajax({
        url: refresh_url,
        type: "GET",
        success: function(response){
            //controllo il warning
            toggleWarning(response.warning);
            //se non nascosto aggiorno
            if (!isHidden(content)) {
                //confronto la data e aggiorno
                if (date.placeholder != response.date) {
                    refreshInput(date, response.date);
                }
                //confronto con i dati e aggiorno
                let are_equal = arrayEqual(placeholders(), response.array);
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
