var ws;
var d = new Date();

function createChatEntry(msgdate, username, message) {
    var entry = document.createElement("div");
    entry.class = "chat_entry";

    var dom_msgdate = document.createElement("span");
    dom_msgdate.class = "chat_msgdate";
    dom_msgdate.innerHTML = msgdate + " ";
    entry.appendChild(dom_msgdate);

    var dom_uname = document.createElement("span");
    dom_uname.class = "chat_username";
    dom_uname.innerHTML = username + ": ";
    entry.appendChild(dom_uname);

    var dom_msg = document.createElement("span");
    dom_msg.class = "chat_message";
    dom_msg.innerHTML = message;
    entry.appendChild(dom_msg);

    return entry;
}

function openWS(messageContainer) {
    ws = new WebSocket("ws://" + window.location.host + "/chat");
    ws.onmessage = function (e) {
        var data = JSON.parse(e.data);
        messageContainer.appendChild(createChatEntry(data.msgdate, data.author, data.message));
        var chat = $('#chat');
        chat.scrollTop(chat.prop("scrollHeight"));
    };
    ws.onclose = function (e) {
        openWS(messageContainer);
    };
}

function sendMessage() {
    var d = new Date();
    var data = { msgdate: "[" + twoDigits(d.getHours()) + ":" + twoDigits(d.getMinutes()) + ":" + twoDigits(d.getSeconds()) + "]",
        author: document.getElementById("username").value,
        message: document.getElementById("message").value };

    if (data.author && data.message) {
        ws.send(JSON.stringify(data));
    }
    document.getElementById("message").value = "";
}

var msgdate = "[" + twoDigits(d.getHours()) + ":" + twoDigits(d.getMinutes()) + ":" + twoDigits(d.getSeconds()) + "]";
var messageContainer = document.getElementById("chat");
if ("WebSocket" in window) {
    openWS(messageContainer);
}
else {
    noty({
        text: "Your browser does not support WebSockets. The chat won't work.",
        layout: "center",
        type: "error"
    });
}