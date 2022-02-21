setInterval(function () {
    $.ajax({
        url: url,
        type: "GET",
        success: function (response) {
            $("#graph").html(response.graph_code);
        }
    });
}, 10000);
