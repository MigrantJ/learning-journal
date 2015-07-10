$(function() {
    $(".hide-on-start").hide();

    $(".journal-list-item").on("click", function (event) {
        event.preventDefault();

        var id = $(this).attr("id").split("-")[1];

        $.ajax({
            method: "GET",
            url: "/detail/" + id
        })
        .done(function(response) {
            $("#entry-title").html(response.entry.title);
            $("#entry-text").html(response.entry.text);
            $("#journal-list").hide();
            $(".journal-entry").show();
        });
    });

    $("#create-button").on("click", function (event) {
        event.preventDefault();

        $("#edit-form-header").text("Create Entry");
        $("#journal-list").hide();
        $("#edit-form-container").show();
    });

    $("#edit-button").on("click", function (event) {
        event.preventDefault();

        var id = $("#form-id").val();

        $.ajax({
            method: "GET",
            url: "/edit/" + id
        })
        .done(function(response) {
            $("#form-title").val(response.entry.title);
            $("#form-text").val(response.entry.text);
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
                title: title,
                text: text
            }
        })
        .done(function(response) {
            $("#entry-title").html(response.entry.title);
            $("#entry-text").html(response.entry.text);
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
