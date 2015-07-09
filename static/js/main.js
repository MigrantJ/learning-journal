$(function() {
    $(".hide-on-start").hide();

    $("#edit-button").on("click", function (event) {
        event.preventDefault();
        $(".journal-entry").hide();
        $("#edit-form-container").show();
    });

    $("#save-button").on("click", function (event) {
        event.preventDefault();

        var id = $("#entry-id").val();
        var title = $("#title").val();
        var text = $("#text").val();

        $.ajax({
            method: "POST",
            url: "/edit/" + id,
            data: {
                id: id,
                title: title,
                text: text
            }
        })
            .done(function() {
                alert(id);
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
