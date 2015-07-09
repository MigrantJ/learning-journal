$(function() {
    $(".hide-on-start").hide();

    $("#edit-button").on("click", function (event) {
        event.preventDefault();

        var id = $("#form-id").val();

        $.ajax({
            method: "GET",
            url: "/edit/" + id
        })
            .done(function(response) {
                $("#form-title").val(response.title);
                $("#form-text").val(response.text);
                $(".journal-entry").hide();
                $("#edit-form-container").show();
            })
            .fail(function() {
                alert( "error" );
            });
    });

    $("#save-button").on("click", function (event) {
        event.preventDefault();

        var id = $("#form-id").val();
        var title = $("#form-title").val();
        var text = $("#form-text").val();

        $.ajax({
            method: "POST",
            url: "/edit/" + id,
            data: {
                id: id,
                title: title,
                text: text
            }
        })
            .done(function(response) {
                $("#entry-title").html(response.title);
                $("#entry-text").html(response.text);
                $(".journal-entry").show();
                $("#edit-form-container").hide();
            })
            .fail(function() {
                alert( "error" );
            });
    });

    $(".cancel-button").on("click", function (event) {
        event.preventDefault();
        $(".journal-entry").show();
        $("#edit-form-container").hide();
    });
});
