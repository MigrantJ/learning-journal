$(function() {
    $(".hide-on-start").hide();

    $("#edit-button").on("click", function (event) {
        event.preventDefault();
        $(".journal-entry").hide();
        $("#edit-form-container").show();
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
                alert(response.text);
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
