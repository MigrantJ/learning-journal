$(function() {
    $(".hide-on-start").hide();

    $(".journal-list-item").on("click", function (event) {
        event.preventDefault();

        var id = $(this).attr("id").split("-")[1];
        $("#form-url").val('/edit/' + id);

        $.ajax({
            method: "GET",
            url: "/detail/" + id
        })
        .done(function(response) {
            $("#entry-title").html(response.entry.title);
            $(".twitter-share-button").attr({
                "data-text": response.entry.title,
                "data-url": window.location.href + 'detail/' + id
            });
            !function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+'://platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document, 'script', 'twitter-wjs');
            $("#entry-text").html(response.entry.text);
            $("#journal-list").hide();
            $(".journal-entry").show();
        });
    });

    $("#create-button").on("click", function (event) {
        event.preventDefault();

        $("#edit-form-header").text("Create Entry");
        $("#form-url").val('/add');
        $("#form-title").val('');
        $("#form-text").val('');
        $("#journal-list").hide();
        $(".journal-entry").hide();
        $("#edit-form-container").show();
    });

    $("#edit-button").on("click", function (event) {
        event.preventDefault();

        var url = $("#form-url").val();

        $.ajax({
            method: "GET",
            url: url
        })
        .done(function(response) {
            $("#edit-form-header").text("Edit Entry");
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

        var title = $("#form-title").val();
        var text = $("#form-text").val();
        var url = $("#form-url").val();

        $.ajax({
            method: "POST",
            url: url,
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
});
