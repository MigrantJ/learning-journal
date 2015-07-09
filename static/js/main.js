$(function() {
    $(".hide-on-start").hide();

    $("#edit-button").on("click", function (event) {
        event.preventDefault();
        $(".journal-entry").hide();
        $("#edit-form-container").show();
    });

    $(".cancel-button").on("click", function (event) {
        event.preventDefault();
        $(".journal-entry").show();
        $("#edit-form-container").hide();
    });
});
