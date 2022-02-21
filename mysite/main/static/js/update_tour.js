setInterval(function () {
    if (is_valid) {
        //controllo se uno dei due differisce
        var updated_array = !arrayEqual(placeholders(), values());
        var updated_date = Boolean(date.placeholder != date.value);
        //uso ajax per fare la richiesta
        if (updated_array || updated_date) {
            $.ajax({
                url: update_url,
                type: "POST",
                dataType: "json",
                data: {
                    "csrfmiddlewaretoken": csrf_token,
                    "date": date.value,
                    "array": JSON.stringify(values())
                },
                success: function (response) {
                    console.log(response.success);
                },
                error: function (response) {
                    console.log(response.error)
                }
            });
        }
    }
}, 5000);
