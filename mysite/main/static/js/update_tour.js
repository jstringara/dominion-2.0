setInterval(function(){
    //estraggo i nuovi valori dai value della tabella
    let rows = document.getElementById("tour_table").rows;
    var inputs = [];
    let tLength = rows.length;
    for (let i=0; i<tLength; i++) {
        var new_row = [...rows[i].getElementsByTagName('input')].map(u => u.value);
        inputs.push(new_row);
    };
    //estraggo la data
    var date = document.getElementById("date");
    //uso ajax per fare la richiesta
    $.ajax({
        url: update_url,
        type: "POST",
        dataType: "json",
        data: {
            "csrfmiddlewaretoken": csrf_token,
            "date": date.value,
            "array": JSON.stringify(inputs)
        },
    });
}, 5000);
