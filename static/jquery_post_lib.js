function handleAjaxStart(el) {
    el.setAttribute("aria-busy", "true");
}

function handleAjaxComplete(el) {
    el.removeAttribute("aria-busy");
}

$(document).ready(() => {
    const url = window.location.href;
    const submitBtn = document.getElementById("submit");

    $("#login-form").submit((event) => {
        event.preventDefault();

        // declaration
        const usernameEl = document.getElementById("username");
        const passwordEl = document.getElementById("password");
        const username = usernameEl.value;
        const password = passwordEl.value;

        // init
        usernameEl.removeAttribute("aria-invalid");
        passwordEl.removeAttribute("aria-invalid");

        // AJAX call with JQuery
        $.ajax({
            url: '/login',
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            data: JSON.stringify({username: username, password: password}),
            beforeSend: () => {handleAjaxStart(submitBtn)},
            complete: () => {handleAjaxComplete(submitBtn)},
            success: (response) => {
                document.cookie = "token="+response.token;
                const urlParams = new URLSearchParams(window.location.search);
                const nextUrl = urlParams.get('next');
                if (nextUrl) {
                    window.location.href = nextUrl;
                }
                else {
                    window.location.href = '/home';
                }
            },
            error: (xhr) => {
                if (xhr.status === 401) {
                    usernameEl.setAttribute("aria-invalid", "true");
                    passwordEl.setAttribute("aria-invalid", "true");
                }
                // TODO: Error Handling
                alert(xhr.responseText);
            }
        });
    });

    $("#admin-form").submit((event) => {
        event.preventDefault();

        // declaration
        const orgNameEl = document.getElementById("org-name");
        const orgName = orgNameEl.value;

        // AJAX call with JQuery
        $.ajax({
            url: '/org-creation',
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            data: JSON.stringify({name: orgName}),
            beforeSend: () => {handleAjaxStart(submitBtn)},
            complete: () => {handleAjaxComplete(submitBtn)},
            success: (response) => {
                console.log('Success:', response);
            },
            error: (xhr) => {
                console.log('Error:', xhr.responseText);
            }
        });
    });

    $("#create-team-form").submit((event) => {
        event.preventDefault();

        // declaration
        const teamNameEl = document.getElementById("team-name");
        const teamName = teamNameEl.value;

        const urlParts = url.split('/');
        const orgId = urlParts[urlParts.length - 2];

        // AJAX call with JQuery
        $.ajax({
            url: '/org/' + orgId + '/team-creation',
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            data: JSON.stringify({team_name: teamName}),
            beforeSend: () => {handleAjaxStart(submitBtn)},
            complete: () => {handleAjaxComplete(submitBtn)},
            success: (response) => {
                window.location.href = '/org/' + orgId + '/team/' + response.team_id;
            },
            error: (xhr) => {
                alert(xhr.responseText);
            }
        });
    });

    $("#signup-form").submit((event) => {
        event.preventDefault();

        // declaration
        const usernameEl = document.getElementById("username");
        const username = usernameEl.value;
        const password1El = document.getElementById("password1");
        const password2El = document.getElementById("password2");
        const password1 = password1El.value;
        const password2 = password2El.value;

        // init
        usernameEl.removeAttribute("aria-invalid");
        if (password1 != password2) {
            password1El.setAttribute("aria-invalid", "true");
            password2El.setAttribute("aria-invalid", "true");
            return
        } else {
            password1El.removeAttribute("aria-invalid");
            password2El.removeAttribute("aria-invalid");
        }

        // AJAX call with JQuery

        $.ajax({
            url: '/signup',
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            data: JSON.stringify({username: username, password: password1}),
            beforeSend: () => {handleAjaxStart(submitBtn)},
            complete: () => {handleAjaxComplete(submitBtn)},
            success: (response) => {
                window.location.href = '/login';
            },
            error: (xhr) => {
                if (xhr.status === 409) {
                    usernameEl.setAttribute("aria-invalid", "true");
                };
                // TODO: Error Handling
                alert(xhr.responseText);
            }
        });
    });

    $('#logout').on("click", (event) => {
        event.preventDefault();
        $.ajax({
            url: '/logout',
            type: 'POST',
            success: (response) => {
                window.location.href = '/login';
            },
            error: (xhr) => {
                // TODO: Error Handling
                alert(xhr.responseText);
            }
        });
    });

    $('#join-team').on("click", (event) => {
        event.preventDefault();

        const joinTeamBtn = document.getElementById("join-team");
        const pattern = /\/org\/([^/]+)\/team\/([^/]+)/;
        const matches = url.match(pattern);
        const orgId = matches[1];
        const teamId = matches[2];

        $.ajax({
            url: '/org/' + orgId + '/team/' + teamId + '/join-team',
            type: 'POST',
            beforeSend: () => {handleAjaxStart(joinTeamBtn)},
            complete: () => {handleAjaxComplete(joinTeamBtn)},
            success: (response) => {
                location.reload();
            },
            error: (xhr) => {
                // TODO: Error Handling
                alert(xhr.responseText);
            }
        });
    });

    $('#leave-team').on("click", (event) => {
        event.preventDefault();

        const leaveTeamBtn = document.getElementById("leave-team");
        const pattern = /\/org\/([^/]+)\/team\/([^/]+)/;
        const matches = url.match(pattern);
        const orgId = matches[1];
        const teamId = matches[2];

        $.ajax({
            url: '/org/' + orgId + '/team/' + teamId + '/leave-team',
            type: 'POST',
            beforeSend: () => {handleAjaxStart(leaveTeamBtn)},
            complete: () => {handleAjaxComplete(leaveTeamBtn)},
            success: (response) => {
                location.reload();
            },
            error: (xhr) => {
                // TODO: Error Handling
                alert(xhr.responseText);
            }
        });
    });
});