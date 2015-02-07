function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function serverAction(text, url) {
    noty({
        text: "Are you sure you want to " + text + "?",
        layout: "center",
        type: "alert",
        buttons: [
            {addClass: 'btn btn-primary', text: 'Ok', onClick: function ($noty) {

                $noty.close();
                window.open(url, "_self");
            }
            },
            {addClass: 'btn btn-danger', text: 'Cancel', onClick: function ($noty) {
                $noty.close();
                noty({text: 'Action has been canceled.', layout: "center", type: 'success'});
            }
            }
        ]
    });
}

function playerAction(info, action) {
    noty({
        text: "Are you sure you want to " + action + " " + info + "?",
        layout: "center",
        type: "alert",
        buttons: [
            {addClass: 'btn btn-primary', text: 'Ok', onClick: function ($noty) {

                $noty.close();
                $.post("ajax/playeraction", {
                    info: info,
                    action: action,
                    _xsrf: getCookie("_xsrf")
                }, function (data) {
                    var response = jQuery.parseJSON(data);

                    if (response.status == "ERROR") {
                        noty({
                            text: response.msg,
                            layout: "center",
                            type: 'error'
                        });
                    } else {
                        noty({
                            text: response.msg,
                            layout: "center",
                            type: 'success'
                        });
                    }
                });
            }
            },
            {addClass: 'btn btn-danger', text: 'Cancel', onClick: function ($noty) {
                $noty.close();
                noty({
                    text: 'Action has been canceled.',
                    layout: "center",
                    type: 'success'
                });
            }
            }
        ]
    });
}

function stopServer() {
    serverAction("stop the server", "/stopserver");
}

function restartServer() {
    serverAction("restart the server", "/restart");
}

function kickPlayer(player) {
    playerAction(player, "kick");
}

function banPlayer(player) {
    playerAction(player, "ban");
}

function unBanPlayer(player) {
    playerAction(player, "unban");
}

function deletePlayer(player) {
    playerAction(player, "delete");
}

function playQuickMenu(player) {
    $.get("ajax/playerquickmenu.html", {
        playername: player
    }, function(data) {
        noty({
            text: data,
            layout: "center"
        });
    });
}

function twoDigits(n) {
    return n < 10 ? '0' + n : '' + n;
}